/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#include <ares.h>
#include <arpa/inet.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>
struct Result {unsigned calls;ares_status_t status;};
static void callback(void* arg,ares_status_t status,size_t timeouts,const ares_dns_record_t* record) {
 (void)timeouts;(void)record;struct Result* result=arg;++result->calls;result->status=status;
}
static void check(int ok) {if(!ok) {abort();}}
int main(void) {
 setvbuf(stdout,NULL,_IONBF,0);
 check(ares_library_init(ARES_LIB_INIT_ALL)==ARES_SUCCESS);
 int fd=socket(AF_INET,SOCK_DGRAM,0);check(fd>=0);
 struct sockaddr_in address={0};address.sin_family=AF_INET;address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 check(bind(fd,(struct sockaddr*)&address,sizeof(address))==0);
 socklen_t length=sizeof(address);check(getsockname(fd,(struct sockaddr*)&address,&length)==0);
 char local[64];check(snprintf(local,sizeof(local),"127.0.0.1:%u",(unsigned)ntohs(address.sin_port))>0);
 unsigned checks=0;
 for(unsigned repeat=0;repeat<100;++repeat) {
  for(unsigned configured=0;configured<2;++configured) {
   for(unsigned host=0;host<2;++host) {
    ares_channel_t* channel=NULL;check(ares_init_options(&channel,NULL,0)==ARES_SUCCESS);
    check(ares_set_servers_csv(channel,configured?local:"192.0.2.53")==ARES_SUCCESS);
    struct Result result={0};
    ares_status_t status=ares_query_dnsrec(channel,host?"pending.example":"localhost",ARES_CLASS_IN,ARES_REC_TYPE_A,callback,&result,NULL);
    size_t pending=ares_queue_active_queries(channel);
    if(repeat==0) {printf("configured=%u host=%u query=%d callbacks=%u callback_status=%d pending=%zu\n",configured,host,status,result.calls,result.status,pending);}
    if(configured) {
     check(status==ARES_SUCCESS&&result.calls==0&&pending==1);
     ares_cancel(channel);check(result.calls==1&&result.status==ARES_ECANCELLED);
    } else {
     check(result.calls==1&&pending==0);
     check(status==ARES_ETIMEOUT&&result.status==ARES_ECONNREFUSED);
    }
    ares_destroy(channel);++checks;
   }
  }
 }
 check(close(fd)==0);ares_library_cleanup();printf("PASS: %u isolated DNS lifetime checks\n",checks);
}
