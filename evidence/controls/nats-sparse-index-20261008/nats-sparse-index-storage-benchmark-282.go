// Copyright 2026 Qore Technologies, s.r.o.
// SPDX-License-Identifier: Apache-2.0
package server

func BenchmarkMemStoreSparseIndexStorage(b *testing.B) {
    for _, subjects := range []int{1, 16, 10000} {
        b.Run(fmt.Sprintf("subjects=%d", subjects), func(b *testing.B) {
            names := make([]string, subjects)
            for i := range names { names[i]=fmt.Sprintf("subject.%d",i) }
            payload:=[]byte("payload")
            b.ReportAllocs()
            b.ResetTimer()
            for b.Loop() {
                b.StopTimer()
                ms,err:=newMemStore(&StreamConfig{Storage:MemoryStorage})
                require_NoError(b,err)
                b.StartTimer()
                for i:=0;i<10000;i++ {
                    _,_,err=ms.StoreMsg(names[i%subjects],nil,payload,0)
                    require_NoError(b,err)
                }
                b.StopTimer()
                require_NoError(b,ms.Stop())
                b.StartTimer()
            }
        })
    }
}
