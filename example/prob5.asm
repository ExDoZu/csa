.data
input:
    0
output:
    0
max:
    20
smallest:
    1
i:
    2
j:
    0
default_start: 
    2
divider:
    1

mul_const:
    10
toascii:
    48

.text
loop:
    load smallest
    mod i
    jz next

    load default_start
    store j
    loop2:
        load j
        mul smallest
        mod i 
        jnz next2

            load smallest
            mul j
            store smallest
            jmp next

        next2:
        load j
        inc
        store j
        sub i
        dec
        jnz loop2


    next:
    load i
    inc
    store i
    sub max
    dec
    jnz loop


inc_div:
    load divider
    mul mul_const
    store divider
    load smallest
    div divider
    jnz inc_div
load divider
div mul_const
store divider

print:
load smallest
div divider
mod mul_const
add toascii
store output

load divider
div mul_const
store divider
jnz print
halt