/* Copyright 2026 Qore Technologies, s.r.o.; MIT. */
#include "sqlite3.c"
#undef NDEBUG
#include <assert.h>
#include <stdio.h>
static sqlite3_mem_methods original;
static int fail_at, allocations;
static int fail_this(void) { return fail_at > 0 && ++allocations == fail_at; }
static void* controlled_malloc(int n) { return fail_this() ? NULL : original.xMalloc(n); }
static void* controlled_realloc(void* p,int n) { return fail_this() ? NULL : original.xRealloc(p,n); }
static void sql(sqlite3* db, const char* text) {
  char* error = NULL;
  int rc = sqlite3_exec(db,text,NULL,NULL,&error);
  if(rc != SQLITE_OK) { fprintf(stderr,"SQL failure %d: %s\n",rc,error); }
  sqlite3_free(error);
  assert(rc == SQLITE_OK);
}
static double number(sqlite3* db, const char* text) {
  sqlite3_stmt* stmt = NULL;
  assert(sqlite3_prepare_v2(db,text,-1,&stmt,NULL)==SQLITE_OK);
  assert(sqlite3_step(stmt)==SQLITE_ROW);
  double n = sqlite3_column_double(stmt,0);
  assert(sqlite3_step(stmt)==SQLITE_DONE);
  assert(sqlite3_finalize(stmt)==SQLITE_OK);
  return n;
}
static int coordinates(sqlite3_rtree_geometry* geom,int count,sqlite3_rtree_dbl* values,int* within) {
  int dimension=*(int*)geom->pContext;
  assert(count==dimension*2);
  for(int i=0;i<count;i+=2) { assert(values[i]==i && values[i+1]==i+2); }
  *within=1;
  return SQLITE_OK;
}
static int conflicts(void* context,int reason,sqlite3_changeset_iter* iter) {
  int* count=context;
  assert(reason==SQLITE_CHANGESET_FOREIGN_KEY);
  int n=0;
  assert(sqlite3changeset_fk_conflicts(iter,&n)==SQLITE_OK && n==1);
  ++*count;
  return SQLITE_CHANGESET_OMIT;
}
static void bounded_varints(void) {
  const int values[] = {0,1,127,128,16383,16384,0x0fffffff,0x7fffffff};
  for(size_t i=0;i<sizeof(values)/sizeof(values[0]);++i) {
    u8 encoded[16]={0};
    int n=sessionVarintPut(encoded,values[i]);
    for(int available=0;available<=12;++available) {
      u8* input=malloc(available ? (size_t)available : 1);
      assert(input!=NULL);
      memcpy(input,encoded,available);
      u8 padded[16]={0};memcpy(padded,encoded,available);
      int actual=0,expected=0;
      int actual_n=sessionVarintGetSafe(input,available,&actual);
      int expected_n=sessionVarintGet(padded,&expected);
      assert(actual==expected && actual_n==expected_n);
      if(available>=n) { assert(actual==values[i] && actual_n==n); }
      free(input);
    }
  }
}
static void change_values(void) {
  const int lengths[]={0,1,2,127,128,16383,16384,65536};
  sqlite3* db=NULL;sqlite3_changegroup* group=NULL;
  assert(sqlite3_open(":memory:",&db)==SQLITE_OK);
  sql(db,"CREATE TABLE t(id INTEGER PRIMARY KEY,value)");
  assert(sqlite3changegroup_new(&group)==SQLITE_OK);
  assert(sqlite3changegroup_schema(group,db,"main")==SQLITE_OK);
  assert(sqlite3changegroup_change_text(group,1,1,"unused",-1)==SQLITE_MISUSE);
  for(int kind=0;kind<2;++kind) {
    for(size_t i=0;i<sizeof(lengths)/sizeof(lengths[0]);++i) {
      int length=lengths[i];char* value=malloc((size_t)length+1);
      assert(value!=NULL);memset(value,'x',length);value[length]=0;
      assert(sqlite3changegroup_change_begin(group,SQLITE_INSERT,"t",0,NULL)==SQLITE_OK);
      assert(sqlite3changegroup_change_int64(group,1,0,1)==SQLITE_OK);
      int rc=kind ? sqlite3changegroup_change_blob(group,1,1,value,length)
                  : sqlite3changegroup_change_text(group,1,1,value,length);
      assert(rc==SQLITE_OK);
      SessionBuffer* buf=&group->cd.aBuf[1];
      int encoded_length=0;
      int count=sessionVarintGet(buf->aBuf+1,&encoded_length);
      assert(encoded_length==length && buf->nBuf==1+count+length);
      assert(memcmp(buf->aBuf+1+count,value,length)==0);
      assert(sqlite3changegroup_change_finish(group,1,NULL)==SQLITE_OK);
      free(value);
    }
  }
  const char utf8[]="a\xc3\xa9\xe2\x82\xac";
  for(int length=-3;length<=6;++length) {
    assert(sqlite3changegroup_change_begin(group,SQLITE_INSERT,"t",0,NULL)==SQLITE_OK);
    assert(sqlite3changegroup_change_text(group,1,1,utf8,length)==SQLITE_OK);
    SessionBuffer* buf=&group->cd.aBuf[1];int actual=0;
    int count=sessionVarintGet(buf->aBuf+1,&actual);
    assert(actual==(length<0?6:length));
    assert(memcmp(buf->aBuf+1+count,utf8,actual)==0);
    assert(sqlite3changegroup_change_finish(group,1,NULL)==SQLITE_OK);
  }
  const int too_large[]={SESSION_MAX_BUFFER_SZ-5,SESSION_MAX_BUFFER_SZ,0x7ffffff9,0x7ffffffe,0x7fffffff};
  for(int kind=0;kind<2;++kind) {
    for(size_t i=0;i<sizeof(too_large)/sizeof(too_large[0]);++i) {
      assert(sqlite3changegroup_change_begin(group,SQLITE_INSERT,"t",0,NULL)==SQLITE_OK);
      /* The allocation must fail before accessing any source byte. */
      const char source_byte=0;
      int rc=kind ? sqlite3changegroup_change_blob(group,1,1,&source_byte,too_large[i])
                  : sqlite3changegroup_change_text(group,1,1,&source_byte,too_large[i]);
      assert(rc==SQLITE_NOMEM);
      assert(sqlite3changegroup_change_finish(group,1,NULL)==SQLITE_OK);
    }
  }
  sqlite3changegroup_delete(group);
  assert(sqlite3_close(db)==SQLITE_OK);
}
int main(void) {
  bounded_varints();
  change_values();
  sqlite3* db=NULL;
  assert(sqlite3_open(":memory:",&db)==SQLITE_OK);
  for(int kind=0;kind<2;++kind) {
    for(int dimension=1;dimension<=5;++dimension) {
      char statement[512];
      int pos=snprintf(statement,sizeof statement,"CREATE VIRTUAL TABLE r USING %s(id",kind?"rtree_i32":"rtree");
      for(int i=0;i<dimension;++i) { pos+=snprintf(statement+pos,sizeof statement-pos,",x%d,y%d",i,i); }
      snprintf(statement+pos,sizeof statement-pos,")"); sql(db,statement);
      pos=snprintf(statement,sizeof statement,"INSERT INTO r VALUES(1");
      for(int i=0;i<dimension;++i) { pos+=snprintf(statement+pos,sizeof statement-pos,",%d,%d",2*i,2*i+2); }
      snprintf(statement+pos,sizeof statement-pos,")"); sql(db,statement);
      assert(sqlite3_rtree_geometry_callback(db,"coords",coordinates,&dimension)==SQLITE_OK);
      assert(number(db,"SELECT count(*) FROM r WHERE id MATCH coords()")==1);
      Rtree tree={0}; RtreeCell cell={0}; tree.nDim=dimension; tree.eCoordType=kind?RTREE_COORD_INT32:RTREE_COORD_REAL32;
      for(int i=0;i<dimension*2;i+=2) {
        if(kind) { cell.aCoord[i].i=i; cell.aCoord[i+1].i=i+2; }
        else { cell.aCoord[i].f=i; cell.aCoord[i+1].f=i+2; }
      }
      assert(cellArea(&tree,&cell)==(1<<dimension));
      sql(db,"DROP TABLE r");
    }
  }
  sql(db,"CREATE TABLE polygons(p); INSERT INTO polygons VALUES('[[0,0],[2,0],[2,2],[0,2],[0,0]]'),('[[3,3],[4,3],[4,4],[3,4],[3,3]]')");
  assert(number(db,"SELECT geopoly_area(geopoly_group_bbox(p)) FROM polygons")==16);
  sql(db,"INSERT INTO polygons VALUES(NULL),('invalid')");
  assert(number(db,"SELECT geopoly_area(geopoly_group_bbox(p)) FROM polygons")==16);
  assert(sqlite3_close(db)==SQLITE_OK);
  sqlite3 *src=NULL,*dest=NULL; sqlite3_session* session=NULL;
  assert(sqlite3_open(":memory:",&src)==SQLITE_OK && sqlite3_open(":memory:",&dest)==SQLITE_OK);
  const char* schema="CREATE TABLE p(id INTEGER PRIMARY KEY); CREATE TABLE c(id INTEGER PRIMARY KEY,pid REFERENCES p(id));";
  sql(src,schema);sql(dest,schema);sql(dest,"PRAGMA foreign_keys=ON");
  assert(sqlite3session_create(src,"main",&session)==SQLITE_OK);
  assert(sqlite3session_attach(session,"c")==SQLITE_OK);
  sql(src,"INSERT INTO c VALUES(1,99)");
  int size=0,nconflicts=0;void* changes=NULL;
  assert(sqlite3session_changeset(session,&size,&changes)==SQLITE_OK);
  assert(sqlite3changeset_apply(dest,size,changes,NULL,conflicts,&nconflicts)==SQLITE_OK);
  assert(nconflicts==1);
  sqlite3_free(changes);sqlite3session_delete(session);
  assert(sqlite3_close(src)==SQLITE_OK && sqlite3_close(dest)==SQLITE_OK);
  assert(sqlite3_shutdown()==SQLITE_OK);
  assert(sqlite3_config(SQLITE_CONFIG_GETMALLOC,&original)==SQLITE_OK);
  sqlite3_mem_methods methods=original;methods.xMalloc=controlled_malloc;methods.xRealloc=controlled_realloc;
  assert(sqlite3_config(SQLITE_CONFIG_MALLOC,&methods)==SQLITE_OK);
  for(int failure=1;failure<=250;++failure) {
    assert(sqlite3_open(":memory:",&db)==SQLITE_OK);
    fail_at=failure;allocations=0;
    int rc=sqlite3_exec(db,"CREATE TABLE a(x TEXT COLLATE NOCASE,y COLLATE RTRIM); CREATE VIEW b AS SELECT x AS c,y AS d FROM a; SELECT * FROM b;",NULL,NULL,NULL);
    fail_at=0;
    assert(rc==SQLITE_OK || rc==SQLITE_NOMEM);
    assert(sqlite3_close(db)==SQLITE_OK);
  }
  assert(sqlite3_shutdown()==SQLITE_OK);
  assert(sqlite3_config(SQLITE_CONFIG_MALLOC,&original)==SQLITE_OK);
  puts("104 bounded varints, 36 change-value cases, 10 RTree dimension/type paths, GeoPoly, deferred FK and 250 allocation failures passed");
  return 0;
}
