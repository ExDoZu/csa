.data
input:
    0
output:
    0
text1:
    "What is your name?"
text2:
    "Hello, "
text3:
    "!"
new_line_code:
    10

counter:
    0
last_addr:
    0

buffer:
    0

.text
load text1
store counter
mov text1 
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

load new_line_code
store output

mov buffer 
inc
store last_addr

input_loop:
    load input
    sub new_line_code
    jz input_break
    add new_line_code
    st last_addr
    
    load last_addr
    inc
    store last_addr

    load buffer
    inc 
    store buffer

    jmp input_loop
input_break:

load text2
store counter
mov text2 
store last_addr
loop2:
    load last_addr
    inc
    store last_addr
    
    ld last_addr
    store output
    
    load counter
    dec
    store counter
    jnz loop2

load buffer
store counter
mov buffer 
store last_addr
loop3:
    load last_addr
    inc
    store last_addr
    
    ld last_addr
    store output
    
    load counter
    dec
    store counter
    jnz loop3


load text3
store counter
mov text3 
store last_addr
loop4:
    load last_addr
    inc
    store last_addr
    
    ld last_addr
    store output
    
    load counter
    dec
    store counter
    jnz loop4

halt
