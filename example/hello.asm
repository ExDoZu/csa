.data
input:
0
output:
0
text:
"Hello, World!"
counter:
0
last_addr:
0
.text
load text
store counter
mov text 
store last_addr
loop:
    load last_addr
    inc
    store last_addr
    
    ld last_addr
    
    store output
    
    load counter
    dec
    store counter
    jnz loop
halt
