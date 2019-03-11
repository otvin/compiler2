;----------------------------------------------------------------------
;				NSM64 Library for x86-64 
;				Copyright 2015 Soffian Abdul Rasad
;				soffianabdulrasad @ gmail.com
;----------------------------------------------------------------------
;This program is free software: you can redistribute it and/or modify
;it under the terms of the GNU General Public License as published by
;the Free Software Foundation, either version 3 of the License, or
;(at your option) any later version.

;This program is distributed in the hope that it will be useful,
;but WITHOUT ANY WARRANTY; without even the implied warranty of
;MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;GNU General Public License for more details.

;You should have received a copy of the GNU General Public License
;along with this program.  If not, see <http://www.gnu.org/licenses/>.
;----------------------------------------------------------------------
;This library is for 64-bit Linux
;Arguments in: RDI RSI RDX or XMM0 for floating point
;Returns in  : RAX or XMM0
;---------------------------------
;To produce a linkable library object,
;Disable everything in the CODING AREA
;and enable this line below
%include 'nobjlist.inc'

;Compile: nasm -f elf64 nsm64.asm -o nsm64.o
;---------------------------------------------

;---------------- CODING AREA ----------------
;To produce an executable...
;compile: nasm -f elf64 nsm64.asm
;link	: ld nsm64.o -o nsm64
;---------------------------------------------
;global _start

;section .data
;y dq -0.0,1937.43
;z dq 34.55,-9.87
;x dd 1.2,2.3,3.4,4.5

;section .text
;_start:
	
;	mov rdi, 256
;        call prtdec
;	call 	exit
;---------------- CODING AREA ----------------;

;------------------------------------
;#1		: prtreg(1)
;OBJ	: Display 64-bit register
;------------------------------------
;RDI	: Register to display
;		> reg64
;------------------------------------
;NOTE	: 16-digit Hex format
;RETN	: -
;------------------------------------
prtreg:
	push 	rbp	          
	mov 	rbp,rsp	
	sub 	rsp,16		 
	push 	rdi
	push 	rax
	push 	rcx
	push 	rsi
	push	rdx
	mov 	rsi,rdi
	cld
	lea 	rdi,[rbp-16] 
	xor 	rax,rax
	mov 	ecx,16
.begin:
	shld 	rax,rsi,4
	add 	al,30h	
	cmp 	al,39h	
	jbe 	.go
	add 	al,7	
.go:
	stosb
	xor 	al,al
	rol 	rsi,4	
	loop 	.begin	
.disp:
	mov		rdx,16 			;Size
	lea		rsi,[rbp-16]	;Address of string
	mov 	edi,1			;stdout
	mov 	eax,1			;sys_write
	syscall
	pop		rdx
	pop 	rsi 
	pop 	rcx	
	pop 	rax
	pop 	rdi
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------
;#2		: dumpreg(0)
;OBJ	: Display Register Dump
;------------------------------------------
;ARG	: -
;------------------------------------------
;NOTE	: RIP - surface address of the function
;		: RSP & RBP - is function-bound
;RETN	: -
;------------------------------------------ 
dumpreg:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16
	push 	r15 
	push 	r14 
	push 	r13 
	push 	r12 
	push 	r11 
	push 	r10 
	push 	r9 
	push 	r8
	push 	rsp 
	push 	rbp 
	push 	rdi 
	push 	rsi 
	push 	rdx 
	push 	rcx 
	push 	rbx 
	push 	rax
	push 	r15 
	push 	r14 
	push 	r13 
	push 	r12 
	push 	r11 
	push 	r10 
	push 	r9 
	push 	r8
	push 	rsp 
	push 	rbp 
	push 	rdi 
	push 	rsi 
	push 	rdx 
	push 	rcx 
	push 	rbx 
	push 	rax
	mov 	dword[rbp-4],'RAX:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'RBX:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'RCX:'
	pop 	rax
	call 	.disp
	call 	newline
	mov 	dword[rbp-4],'RDX:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'RSI:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'RDI:'
	pop 	rax
	call 	.disp
	call 	newline
	mov 	dword[rbp-4],'RBP:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'RSP:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'R8 :'
	pop 	rax
	call 	.disp
	call 	newline
	mov 	dword[rbp-4],'R9 :'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'R10:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'R11:'
	pop 	rax
	call 	.disp
	call 	newline
	mov 	dword[rbp-4],'R12:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'R13:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'R14:'
	pop 	rax
	call 	.disp
	call 	newline
	mov 	dword[rbp-4],'R15:'
	pop 	rax
	call 	.disp
	mov 	dword[rbp-4],'RIP:'
	mov		rax,[rbp+8]
	sub		rax,5
	call 	.disp
	jmp 	.done
.disp:
	mov 	esi,4
	lea		rdi,[rbp-4]
	call	prtstr
	mov		rdi,rax
	call 	prtreg
	mov		al,' '
	call	prtchr
	ret
.done:
	pop		rax 
	pop 	rbx 
	pop 	rcx 
	pop 	rdx 
	pop 	rsi 
	pop		rdi 
	pop 	rbp 
	pop 	rsp
	pop		r8
	pop 	r9
	pop 	r10
	pop 	r11 
	pop 	r12
	pop 	r13
	pop 	r14
	pop 	r15
	mov 	rsp,rbp
	pop 	rbp
	ret
;-------------------------------------
;#3		: flags(1)
;OBJ	: Display 64-bit flag register
;-------------------------------------
;ARG	: Push the flag register
;		> pushfq
;-------------------------------------
;NOTE	: Argument on the stack
;RETN	: -
;-------------------------------------
flags:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16
	push 	rsi 
	push 	rdi 
	push	rax
	push	rdx
	pushfq
	cld
	lea		rdi,[rbp-12]
	mov 	dword[rdi],"OD  "
	mov 	dword[rdi+4],"SZ A"
	mov 	dword[rdi+8]," P C"
	mov		esi,12
	call	prtstr
	call 	newline
	mov 	rax,[rbp+16]
	xor		edx,edx
	mov		esi,11
	mov		rdi,rax
	call 	bitfield
	popfq
	pop		rdx
	pop 	rax
	pop 	rdi
	pop 	rsi
	mov 	rsp,rbp
	pop 	rbp
	ret		8
;--------------------------------------------
;#4		: prtdec(2)
;OBJ	: Display & Convert to 64-bit Decimal
;--------------------------------------------
;RDI	: Value to display.
;	    > [dq],imm,reg64
;--------------------------------------------
;NOTE	: Signed.
;RETN	: -
;--------------------------------------------
prtdec: 
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,32
	push	rdi
	push 	rsi 
	push 	rdx
	push 	rcx
	push	rax 
	push 	rbx
	push 	r9
	push 	r15 
	push 	r11
	cld
	mov		r15,rdi
	xor		r11,r11
	xor		r9,r9
	lea 	rdi,[rbp-24]
	mov 	rax,r15
	test 	rax,rax
	jns 	.pdc1
	mov 	al,'-'
	stosb
	inc		r11
	neg 	r15
.pdc1:
	mov 	rax,r15
	mov 	rcx,0cccccccccccccccdh
	mul 	rcx
	shr 	rdx,3		
	mov 	rsi,rdx		
	mov 	rax,rdx
	mov 	ebx,10
	mul 	rbx 		
	mov 	rcx,r15	
	sub 	rcx,rax		
	push 	rcx		
	test 	rsi,rsi
	jz 		.tmp3
	inc 	r9
	mov 	r15,rsi	
	jmp 	.pdc1
.tmp3:	
	test 	rbx,rbx
	jz 		.pdc2
.pdc2:	
	pop 	rax
	add 	al,30h
	stosb
	inc		r11
	test 	r9,r9
	jz 		.pdc3
	dec 	r9
	jmp 	.pdc2
.pdc3:
	mov 	rsi,r11
	lea 	rdi,[rbp-24]
	call	prtstr
.pdcz:
	pop		r11 
	pop 	r15 
	pop 	r9
	pop 	rbx 
	pop 	rax 
	pop		rcx 
	pop 	rdx 
	pop 	rsi 
	pop 	rdi
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#5		: prtdecu(1)
;OBJ	: Display unsigned 64-bit Decimal
;------------------------------------------------
;RDI	: Value to display.
;	    > [dq],imm,reg64
;------------------------------------------------
;NOTE	: -
;RETN	: -
;------------------------------------------------
prtdecu: 
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,32
	push	rax
	push	rcx
	push	rsi
	push	rdi
	push	rdx
	mov		rax,rdi
	cld		
	lea		rdi,[rbp-20]
	mov		rcx,10
	xor		rsi,rsi
.div:
	xor		rdx,rdx
	div		rcx
	push	rdx
	inc		rsi
	test	rax,rax
	jz		.ok
	jmp		.div
.ok:	
	dec		rsi
	pop		rax
	add		al,30h
	stosb
	test	rsi,rsi
	jz		.disp
	jmp		.ok
.disp:
	xor		al,al
	stosb
	lea		rdi,[rbp-20]
	call	prtstrz	
	pop		rdx
	pop		rdi
	pop		rsi
	pop		rcx
	pop		rax
	mov 	rsp,rbp
	pop 	rbp
	ret
;-------------------------------------------
;#6		: prthex(1)
;OBJ	: Display 64-bit Hexadecimal
;-------------------------------------------
;RDI	: Value to display.
;	    > [dq],imm,reg64
;-------------------------------------------
;NOTE	: Immediate must be in valid hex format
;RETN	: -
;-------------------------------------------
prthex:
	push 	rbp	          
    mov 	rbp,rsp	
    sub 	rsp,16
    push	rdi 
    push 	rsi 
    push 	rdx 
    push 	rcx 
    push 	rax
    cld       
    mov		rax,rdi
    lea 	rdi,[rbp-16]
    xor 	rsi,rsi
    mov 	ecx,16
.phx1:
	xor 	rdx,rdx
	div 	rcx
	add 	dl,30h
	cmp 	dl,39h
	jbe 	.o
	add 	dl,7
.o:	
	inc 	rsi
	push 	rdx
	test 	rax,rax
	jz  	.tmp2
	jmp 	.phx1
.tmp2:
	mov 	rcx,rsi	
.phx2:
	dec 	rsi
	pop 	rax
	stosb
	test 	rsi,rsi
	jz 		.phx3
	jmp 	.phx2	
.phx3:
	mov 	rsi,rcx
	lea 	rdi,[rbp-16]
	call	prtstr
.phxz:
	pop		rax 
	pop		rcx 
	pop		rdx 
	pop		rsi 
	pop		rdi
	mov 	rsp,rbp       
    pop 	rbp 
	ret
;------------------------------------------
;#7		: prtoct(1)
;OBJ	: Convert to & Display 64-bit Octal
;------------------------------------------
;RSI	: Signess. 1-sign. 0-unsigned
;		> imm,reg64,[dq]		
;RDI	: Value to display.
;	    > [dq],imm,reg64
;------------------------------------------
;NOTE	: Immediate must be in valid oct format
;RETN	: -
;------------------------------------------
prtoct:
	push 	rbp	          
    mov 	rbp,rsp	
    sub 	rsp,32
    push	rsi 
    push 	rdi 
    push 	rax 
    push 	rbx 
    push 	rdx 
    push 	rcx
    mov 	rax,rdi
    mov 	rdx,rdi
    mov 	rbx,rsi
    mov 	ecx,8
    xor 	rsi,rsi
    cld       
    lea 	rdi,[rbp-24] 
	test 	rbx,rbx
	jz 		.poc1
    test 	rax,rax
	jns 	.poc1
    mov 	al,'-'
    stosb
    inc 	rsi
    mov 	rax,rdx 
    neg 	rax 
.poc1:
	xor 	rdx,rdx
	div 	rcx
	add 	dl,30h
	push 	rdx
	inc 	rsi
	test 	rax,rax
	jz 		.tmp2
	jmp 	.poc1
.tmp2:
	mov 	rdx,rsi	
.phx2:	
	dec 	rsi
	pop 	rax
	stosb
	test 	rsi,rsi
	jz 		.phx3
	jmp 	.phx2	
.phx3:
	mov		rsi,rdx
	lea 	rdi,[rbp-24]
	call	prtstr
	pop		rcx 
	pop 	rdx 
	pop 	rbx 
	pop 	rax 
	pop 	rdi 
	pop 	rsi
	mov 	rsp,rbp       
    pop 	rbp 
	ret
;---------------------------------------------
;#8		: prtbinf(3)
;OBJ	: Convert to & Display 64-bit Binary
;---------------------------------------------
;RDX	: Digit Separator: 1-with, 0-without
;		> imm,reg64,[dq]
;RSI	: Trim. 1-trim. 0-not trimmed
;		> imm,reg64,[dq]		
;RDI	: Value to display.
;	    > [dq],reg64,imm
;---------------------------------------------
;NOTE	: Immediate must be in valid bin format
;RETN	: -
;--------------------------------------------- 
prtbinf:
	push	rbp
	mov		rbp,rsp
	sub		rsp,16*5
	push	rax 
	push	rcx 
	push	rbx 
	push	rdx 
	push 	rdi 
	push	rsi 
	push	r8
	mov		rbx,rdx			;separator
	mov		rdx,rdi 		;val
	mov		r8,rsi  		;trim
	cld
	lea		rdi,[rbp-72] 	;local string
	test	rdx,rdx
	jnz		.ok
	mov		al,'0'
	stosb
	inc		rsi
	jmp		.done
.ok:
	xor		rsi,rsi
	mov		ecx,63
	test	r8,r8
	jz		.start
	bsr		rcx,rdx
.start:	
	mov		al,'0'
	bt		rdx,rcx
	jnc		.uno
	mov		al,'1'
.uno:	
	stosb	
	inc		rsi
	dec		rcx
	js		.done
	test	rbx,rbx
	jnz		.space
	jmp		.start
.space:
	cmp		rcx,47
	je		.spc
	cmp		rcx,31
	je		.spc
	cmp		rcx,15
	je		.spc
	jmp		.start
.spc:
	mov		al,' '
	stosb	
	inc		rsi
	jmp		.start
.done:
	lea		rdi,[rbp-72]
	call	prtstr
	pop		r8 
	pop 	rsi 
	pop 	rdi
	pop		rdx 
	pop 	rbx 
	pop 	rcx 
	pop 	rax
	mov		rsp,rbp
	pop		rbp
	ret	
;------------------------------------------------
;#9		: prtbin(1)
;OBJ	: Convert to & Display 64-bit Binary
;------------------------------------------------
;RDI	: Value to display.
;	    > [dq],reg64,imm
;------------------------------------------------
;NOTE	: Immediate must be in valid bin format
;RETN	: -
;------------------------------------------------ 
prtbin:
	push	rbp
	mov		rbp,rsp
	sub		rsp,16*5
	push	rax 
	push	rcx 
	push	rdx 
	push 	rdi 
	push	rsi 
	xor		rsi,rsi
	xor		rcx,rcx
	mov		rdx,rdi 		;val
	bsr		rcx,rdx
	cld
	lea		rdi,[rbp-72] 	;local string
	test	rdx,rdx
	jnz		.start
	mov		al,'0'
	stosb
	inc		rsi
	jmp		.done
.start:	
	mov		al,'0'
	bt		rdx,rcx
	jnc		.uno
	mov		al,'1'
.uno:	
	stosb	
	inc		rsi
	dec		rcx
	js		.done
	jmp		.start
.done:
	lea		rdi,[rbp-72]
	call	prtstr
	pop 	rbx 
	pop 	rdi
	pop		rdx 
	pop 	rcx 
	pop 	rax
	mov		rsp,rbp
	pop		rbp
	ret	
;------------------------------------------------
;#10	: fpbin(1)
;OBJ	: Convert to & Display 64-bit Floating Point Binary
;------------------------------------------------
;xmm0	: Value to display
;	    > [dq],reg64 (use movq)
;------------------------------------------------
;NOTE	: Variable & Immediate must be of type FP (x.x)
;RETN	: -
;------------------------------------------------
fpbin:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16*5
	push 	rdi 
	push	rdx 
	push	rcx 
	push	rsi 
	push	rax
	movq	rdx,xmm0
	cld
	lea 	rdi,[rbp-66]
	mov 	ecx,63
.prb0:	
	mov		al,'0'
	bt 		rdx,rcx	
	jnc		.tmp0
	mov 	al,'1'
.tmp0:	
	stosb
	test 	rcx,rcx
	jz 		.prb1
	dec 	rcx
	cmp 	rcx,62
	je 		.dot
	cmp 	rcx,51
	je 		.dot
	jmp 	.prb0
.dot:		
	mov		al,'.'
	stosb
	jmp 	.prb0
.prb1:
	mov 	esi,66
	lea 	rdi,[rbp-66]
	call	prtstr
	pop		rax 
	pop 	rsi 
	pop 	rcx 
	pop 	rdx 
	pop 	rdi
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#11	: prtdbl(1)
;OBJ	: Display double precision (REAL8)
;------------------------------------------------
;XMM0	: Value to display
;	    > [dq],reg64 (use movq)
;------------------------------------------------
;NOTE	: Variable should be initialized to FP (0.0)
;		: Variable must be of type DQ.
;		: Displays Exponential notation for large FP
;RETN	: -
;------------------------------------------------
;info	dq 0.0	[rbp-225]
;dblstr	 rb 24  [rbp-217]
;save	 rb 108	[rbp-193]
;mantissa dq 0.0 [rbp-85]
;exponent dq 0   [rbp-77] 
;val1 	 dq 0.0 [rbp-69] 
;val2 	 dq 0.0 [rbp-61]
;copy	 dq 0.0 [rbp-53]
;tmp 	 dq 0   [rbp-45] 
;digit	 dq 0   [rbp-37]
;index	 dq 0   [rbp-29]
;ten	 dq 10.0[rbp-21]
;one	 dq 1.0 [rbp-13] 
;control dw 0   [rbp-5]
;finish	 db 0   [rbp-3]
;Small	 db 0   [rbp-2]
;Big	 db 0   [rbp-1]
;------------------------
prtdbl:
	push	rbp
	mov		rbp,rsp
	sub		rsp,16*15
	push 	rax 
	push	rcx 
	push	rdx 
	push	rsi 
	push	rdi 
	push 	rbx 
	push	r8 
	push	r9 
	push	r10 
	push	r11
	movq	[rbp-225],xmm0
	lea 	rax,[rbp-193]		
	fsave 	[rax]
	push 	rax
	mov		rax,0		
	mov		[rbp-69],rax
	mov		[rbp-61],rax
	mov		[rbp-85],rax
	mov		[rbp-53],rax
	mov		rax,4024000000000000h            	
	mov		[rbp-21],rax
	mov		rax,3FF0000000000000h		
	mov		[rbp-13],rax
	mov		word[rbp-5],0
	mov		byte[rbp-3],0
	mov		byte[rbp-2],0
	mov		byte[rbp-1],0
.start:		
	cld	
	lea		rdi,[rbp-217]
	xor		r11,r11			
	movq	qword[rbp-255],xmm0
	mov 	rax,[rbp-225]
	test 	rax,rax
	jns		.begin
	mov		al,'-'
	stosb
	inc		r11
.begin:
	finit
	fld 	qword[rbp-225]
	fstp 	qword[rbp-53]
	fld		qword[rbp-53]
	xor		rax,rax			
	ftst
	fstsw 	ax
	cmp		eax,7800h
	jz		.zero
	;cmp		eax,3902h
	;jz		.zero
.back:	
	fabs
	fxtract
	fstp 	qword[rbp-85]
	fistp 	qword[rbp-77]
	mov 	rcx,[rbp-77]
	mov 	rdx,[rbp-85]
	mov 	rax,0fffffffffffffh
	and 	rdx,rax
	bts 	rdx,52			;+1.0
	mov 	esi,52
	test 	rcx,rcx
	js  	.small
	cmp		rcx,50
	ja  	.big
;---------------------------
.get_integer:
	bt  	rdx,rsi
	jnc   	.again
	finit
	mov 	[rbp-45],rcx
	fild 	qword[rbp-45]
	fld1
	fscale
	fld 	qword[rbp-69]
	fadd 	st0,st1
	fstp 	qword[rbp-69]
.again:	
	dec		rcx
	js		.tmp0
	dec 	rsi
	jmp 	.get_integer
;----------------------------
.big:	
    finit
	fld 	qword[rbp-53]
	fabs
	xor 	r8,r8
.f:	
	fdiv 	qword[rbp-21]
	inc 	r8
	fcom 	qword[rbp-21]
	fstsw 	ax
	sahf
	jb   	.g
	jmp  	.f
.g:	
	mov 	[rbp-29],r8
	inc 	byte[rbp-1]
	jmp 	.back
;----------------------------
.small:
	xor 	r8,r8
	finit
	fld 	qword[rbp-225]
	fabs
.x:	
	fmul 	qword[rbp-21]
	inc 	r8
	fcom 	qword[rbp-13]
	fstsw 	ax
	sahf
	jae  	.k
	jmp 	.x
.k:		
	mov 	[rbp-29],r8
	fstp 	qword[rbp-53]
	cmp		r8,16 ;17?
	jae		.m
	neg		rcx			  	
	jmp 	.get_fraction
.m:	
	fld 	qword[rbp-53]
	inc 	byte[rbp-2]
	jmp 	.back
;-----------------------------
.tmp0:		
	dec 	rsi
	mov 	ecx,1
;-----------------------------
.get_fraction:
	bt  	rdx,rsi
	jnc  	.go
	mov 	[rbp-45],rcx
	finit
	fild 	qword[rbp-45]
	fchs
	fld1
	fscale
	fld 	qword[rbp-61]
	fadd 	st0,st1
	fstp 	qword[rbp-61]
.go:
	dec		rsi
	js		.tmp1
	inc 	rcx
	jmp 	.get_fraction
;---------------------------
.tmp1:
	finit
	fld 	qword[rbp-69]	;val1
	fistp 	qword[rbp-69]	;val1
	mov		rax,[rbp-69]	;val1
	xor		r8,r8
	mov		ecx,10
;---------------------------
.disp1:		
	xor 	rdx,rdx
	div 	rcx
	push 	rdx
	inc		r8
	test 	rax,rax
	jz  	.trans
	jmp 	.disp1
.trans:
	mov 	r9,r8			;Digits count
.print1:		
	dec 	r8
	pop		rax
	add		al,30h
	stosb
	inc		r11
	test 	r8,r8
	jz  	.tmp2
	jmp 	.print1
;--------------------------
.tmp2:
	cmp 	byte[rbp-3],1
	je   	.quit
	mov		al,'.'
	stosb
	inc 	r11
.no:	
	finit
	fstcw 	[rbp-5]		
	bts 	word[rbp-5],10
	fldcw 	[rbp-5]
	mov 	ebx,16			;Max digits = 17 ??
	mov		r10,r9			;Digits used
	sub 	rbx,r10			;digits left
;--------------------------
.disp2:  
	fld 	qword[rbp-61]
	fmul 	qword[rbp-21]
	fst		qword[rbp-61]
	frndint
	fistp 	qword[rbp-37]
	mov		rax,[rbp-37]
	add		al,30h
	stosb
	inc		r11
	dec 	rbx
	jz   	.done
	fild 	qword[rbp-37]
	fld		qword[rbp-61]
	fsub 	st0,st1
	fstp 	qword[rbp-61]
	ffree 	st1
	jmp 	.disp2
;---------------------------
.done:
	cmp 	byte[rbp-1],0
	je		.nxt
	mov		ax,'e+'
	jmp		.proceed
.nxt:
	cmp		byte[rbp-2],0
	je		.quit
	mov		ax,'e-'
.proceed:
	stosw
	add 	r11,2
	mov 	rax,[rbp-29]
	xor		r8,r8
	mov 	ecx,10
	mov		byte[rbp-3],1
	jmp		.disp1
;---------------------------
.zero:	
	mov		ax,'0.'
	stosw
	mov 	al,'0'
	stosb
	add		r11,3
;---------------------------
.quit:
	pop		rax
	frstor 	[rax]
	mov		rsi,r11
	lea		rdi,[rbp-217]
	call	prtstr
	pop 	r11 
	pop 	r10 
	pop 	r9 
	pop 	r8 
	pop 	rbx 
	pop		rdi 
	pop 	rsi 
	pop 	rdx 
	pop 	rcx 
	pop 	rax
	mov		rsp,rbp
	pop		rbp
	ret
;------------------------------------------------
;#12	: prtflt(1)
;OBJ	: Display single precision (REAL4)
;------------------------------------------------
;xmm0	: Value to display
;		> reg32,[dd] (use movd)
;------------------------------------------------
;NOTE	: Variable should be initialized to FP (0.0)
;		: Variable must be of type DD. Use MOVD
;		: Displays Exponential notation for large FP
;RETN	: -
;------------------------------------------------
;info	 	dd 0.0  [rbp-127]
;fltstr  	rb 10 	[rbp-123]
;save	 	rb 108  [rbp-113]
;mantissa 	dd 0.0 	[rbp-45]
;exponent 	dd 0	[rbp-41]
;val1	 	dd 0.0 	[rbp-37]
;val2	 	dd 0.0 	[rbp-33]
;copy	 	dd 0.0 	[rbp-29]
;tmp	 	dd 0	[rbp-25]
;digit	 	dd 0	[rbp-21]
;index	 	dd 0	[rbp-17]
;ten	 	dd 10.0	[rbp-13]
;one	 	dd 1.0 	[rbp-9]
;control 	dw 0	[rbp-5]
;finish  	db 0	[rbp-3]
;Small	 	db 0	[rbp-2]
;Big	 	db 0	[rbp-1]
;------------------------
prtflt:
	push	rbp
	mov		rbp,rsp
	sub		rsp,128
	push	rax 
	push	rcx 
	push	rdx 
	push	rsi 
	push	rdi 
	push	rbx 
	push	r8 
	push	r9 
	push	r10 
	movd	[rbp-127],xmm0
	bts		dword[rbp-127],0
	lea		rax,[rbp-113]
	fsave	[rax]
	push	rax
	mov		eax,0
	mov		[rbp-37],eax
	mov		[rbp-33],eax
	mov		[rbp-45],eax
	mov		[rbp-29],eax
	mov		eax,41200000h
	mov		[rbp-13],eax
	mov		eax,3F800000h
	mov		[rbp-9],eax
	mov		word[rbp-5],0
	mov		byte[rbp-3],0
	mov		byte[rbp-2],0
	mov		byte[rbp-1],0
.start: 	
	cld	
	lea		rdi,[rbp-123]
	mov		eax,[rbp-127]
	test	eax,eax
	jns		.begin
	mov		al,'-'
	stosb
.begin:
	finit
	fld		dword[rbp-127]
	fstp	dword[rbp-29]
	fld		dword[rbp-29]
	xor		rax,rax
	ftst
	fstsw	ax
	cmp		eax,3802h
	jz		.zero
	cmp		eax,3902h
	jz		.zero
.back:	
	fabs
	fxtract
	fstp	dword[rbp-25]
	fistp	dword[rbp-41]
	mov		ecx,[rbp-41]
	mov		edx,[rbp-25]
	mov		eax,0fffffffh
	and		edx,eax
	bts		edx,23		;+1.0
	mov		esi,23
	test	ecx,ecx
	js		.small
	cmp		ecx,18
	ja		.big
;---------------------------
.get_integer:
	bt		edx,esi
	jnc		.again
	finit
	mov		[rbp-25],ecx
	fild	dword[rbp-25]
	fld1
	fscale
	fld		dword[rbp-37]
	fadd	st0,st1
	fstp	dword[rbp-37]
.again: 
	dec		rcx
	js		.tmp0
	dec		rsi
	jmp		.get_integer
.big:	
	finit
	fld		dword[rbp-29]
	fabs
	xor		r8,r8
.f:	
	fdiv	dword[rbp-13]
	inc		r8
	fcom	dword[rbp-13]
	fstsw	ax
	sahf
	jb		.g
	jmp		.f
.g:	
	mov		[rbp-17],r8d
	inc		byte[rbp-1]
	jmp		.back
.small:
	xor		r8,r8
	finit
	fld		dword[rbp-127]
	fabs
.x:	
	fmul	dword[rbp-13]
	inc		r8
	fcom	dword[rbp-9]
	fstsw	ax
	sahf
	jae		.k
	jmp		.x
.k:		
	mov		[rbp-17],r8d
	fstp	dword[rbp-29]
	cmp		r8,7
	jae		.m
	neg		ecx
	jmp		.get_fraction
.m:	
	fld		dword[rbp-29]
	inc		byte[rbp-2]
	jmp		.back
.tmp0:		
	dec		rsi
	mov		ecx,1
.get_fraction:
	bt		edx,esi
	jnc		.go
	mov		[rbp-25],ecx
	finit
	fild	dword[rbp-25]
	fchs
	fld1
	fscale
	fld		dword[rbp-33]
	fadd	st0,st1
	fstp	dword[rbp-33]
.go:
	dec		esi
	js		.tmp1
	inc		rcx
	jmp		.get_fraction
.tmp1:
	finit
	fld		dword[rbp-37]
	fistp	dword[rbp-37]
	mov		eax,[rbp-37]
	xor		r8,r8
	mov		ecx,10
.disp1:
	xor		rdx,rdx
	div		rcx
	push	rdx
	inc		r8
	test	rax,rax
	jz		.trans
	jmp		.disp1
.trans:
	mov		r9,r8		  ;Digits count
.print1:		
	dec		r8
	pop		rax
	add		al,30h
	stosb
	inc		r11
	test	r8,r8
	jz		.tmp2
	jmp		.print1
.tmp2:
	cmp		byte[rbp-3],1
	je		.quit
	mov		al,'.'
	stosb
.no:	
	finit
	fstcw	[rbp-5] 	
	bts		word[rbp-5],10
	fldcw	[rbp-5]
	mov		ebx,7
	mov		r10,r9
	sub		rbx,r10
.disp2:
	fld		dword[rbp-33]
	fmul	dword[rbp-13]
	fst		dword[rbp-33]
	frndint
	fistp	dword[rbp-21]
	mov		eax,[rbp-21]
	add		al,30h
	stosb
	dec		ebx
	jz		.done
	fild	dword[rbp-21]
	fld		dword[rbp-33]
	fsub	st0,st1
	fstp	dword[rbp-33]
	ffree	st1
	jmp		.disp2
.done:
	cmp		byte[rbp-1],0
	je		.nxt
	mov		ax,'e+'
	jmp		.proceed
.nxt:
	cmp		byte[rbp-2],0
	je		.quit
	mov		ax,'e-'
.proceed:
	stosw
	mov		eax,[rbp-17]
	xor		r8,r8
	mov		ecx,10
	mov		byte[rbp-3],1
	jmp		.disp1
.zero:
	mov		ax,'0.'
	stosw
	mov		al,'0'
	stosb
.quit:
	pop		rax
	frstor	[rax]
	xor		al,al
	stosb
	lea		rdi,[rbp-123]
	call	prtstrz
	pop		r10
	pop		r9
	pop		r8
	pop		rbx
	pop		rdi
	pop		rsi
	pop		rdx
	pop		rcx
	pop		rax
	mov		rsp,rbp
	pop		rbp
	ret
;------------------------------------------------
;#13 	: prtstr(2)
;OBJ	: Display string with size
;------------------------------------------------
;RSI	: Num. of bytes to display/string size
;	    > imm,reg64,[dq]
;RDI	: Address of the string
;	    > add64,reg64
;------------------------------------------------
;NOTE	: Use with getstr
;RETN	: -
;------------------------------------------------
prtstr:	
	push	rdi 
	push	rsi 
	push	rdx 
	push	rax 
	push	rcx
	mov		rdx,rsi ;size
	mov		rsi,rdi	;address
	mov 	edi,1	;stdout
	mov 	eax,edi	;write
	syscall
	pop		rcx 
	pop 	rax 
	pop 	rdx 
	pop 	rsi 
	pop 	rdi
	ret
;------------------------------------------------
;#14	: prtstrz(1)
;OBJ	: Display 0-ended string
;------------------------------------------------
;RDI	: Address of the string
;	    > add64,reg64
;------------------------------------------------
;NOTE	: String array must be 0-ended
;		: Use with getstrz
;RETN	: -
;------------------------------------------------
prtstrz:
	push	rsi
	push	rdx 
	push	rax 
	push	rcx
	push	rdi
	mov		rsi,rdi
	mov		al,0
	mov		rcx,-1
	repne	scasb
	mov		rdx,-2
	sub		rdx,rcx
	mov		edi,1
	mov		eax,1
	syscall
	pop		rdi
	pop 	rcx 
	pop 	rax 
	pop 	rdx 
	pop 	rsi 
	ret
;------------------------------------------------
;#15	: prtchar(1)
;OBJ	: Display a character
;------------------------------------------------
;RDI	: Address of the character
;	    > add64, reg64
;------------------------------------------------
;NOTE	: -
;RETN	: -
;------------------------------------------------
prtchar:	
	push	rax 
	push	rdi
	mov		al,byte[rdi]
	call	prtchr
	pop 	rdi 
	pop 	rax 
	ret
;--------------------------------
;#16	: prtchr(AL)
;OBJ	: Display character in RAX
;--------------------------------
;ARG	: The character in RAX(AL)
;--------------------------------
;NOTE	: For internal use. Use prtchar
;RETN	: 
;--------------------------------
prtchr:
	push	rcx
	push	r11
	push	rdi
	push	rsi
	push	rdx
	push 	rax
	mov 	edx,1
	mov 	rsi,rsp
	mov 	edi,edx
	mov 	eax,edx
	syscall
	pop		rax
	pop		rdx
	pop		rsi
	pop		rdi
	pop		r11
	pop		rcx
	ret
;------------------------------------------------
;#17	: getch(0)/AL
;OBJ	: Get a character from keyboard
;------------------------------------------------
;ARG 	: -
;------------------------------------------------
;NOTE	: Takes single character only
;		: For internal use only. Use getchr.
;RETN	: The key in AL
;------------------------------------------------
getch:
	push 	rbp
	mov		rbp,rsp
	sub 	rsp,16
	push 	rdx
	push 	rdi
	push 	rsi
	lea 	rsi,[rbp-2]
	mov 	edx,1
	xor 	edi,edi
	xor 	eax,eax
	syscall
	xor 	eax,eax
	mov 	al,byte[rbp-2]
	pop 	rsi
	pop 	rdi
	pop 	rdx
	mov 	rsp,rbp
	pop		rbp
	ret
;------------------------------------------------
;#18	: getchr(1)
;OBJ	: Get a character + LF from keyboard
;------------------------------------------------
;RDI	: Address of keeper
;	    > add64, reg64
;------------------------------------------------
;NOTE	: Takes single character only
;		: Variable must be of type DB
;RETN	: Character in the sent address
;------------------------------------------------
getchr:	
	push 	rsi 
	push	rdx 
	push	rdi 
	push	rax
	push	rcx
	mov		rsi,rdi
	mov 	edx,2		;+LF
	xor 	edi,edi		;stdin
	xor		eax,eax		;read
	syscall
	pop		rcx
	pop 	rax 
	pop 	rdi 
	pop 	rdx 
	pop 	rsi
	ret
;------------------------------------------------
;#19	: getstr(2)
;OBJ	: Get string from keyboard
;------------------------------------------------
;RSI	: Size of buffer+LF 
;		> imm,reg64,[dq]	
;RDI	: Address of the buffer to keep the string
;		> add64, reg64
;------------------------------------------------
;NOTE	: String entered must not exceed size
;		: Array or variable must be of type DB
;		: String size must include LF
;RETN	: Number of actual bytes in RAX
;		: String in sent buffer
;------------------------------------------------
getstr:	
	push 	rsi 
	push	rdx 
	push	rdi 
	push	r15 
	push	rcx
	mov		r15,rsi
	mov		rdx,rsi
	mov		rsi,rdi
	xor 	rdi,rdi
	xor 	rax,rax
	syscall
	cmp 	rax,r15
	jbe 	.done
	mov 	rax,r15
.done:	
	pop 	rcx 
	pop 	r15 
	pop 	rdi 
	pop 	rdx 
	pop 	rsi
	ret
;------------------------------------------------
;#20	: getstrz(1)
;OBJ	: Get string from keyboard
;------------------------------------------------
;RDI	: Address of the buffer to keep the string
;	    > add64, reg64
;------------------------------------------------
;NOTE	: String will be 0-ended
;		: Use with prtstrz
;		: Array or variable must be of type DB
;RETN	: String in buffer
;------------------------------------------------
getstrz:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16
	push	rdi 
	push	rsi 
	push	rdx 
	push	rax 
	push	rbx 
	push	r9 
	push	rcx
	mov		rsi,rdi
	xor 	rbx,rbx
	mov 	r9,rsi
	lea 	rsi,[rbp-1] 	
	xor 	rdi,rdi
	mov 	edx,1
	xor 	rax,rax
.rep:
	syscall
	mov 	al,byte[rbp-1]
	cmp 	al,0ah
	je 		.done
	mov 	byte[r9+rbx],al
	inc 	rbx
	xor 	rax,rax
	jmp 	.rep
.done:
	inc 	rbx
	mov 	byte[r9+rbx],0 	;NUL terminated
	pop		rcx 
	pop 	r9 
	pop 	rbx 
	pop 	rax 
	pop 	rdx 
	pop 	rsi 
	pop 	rdi
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#21	: getint(0)/RAX
;OBJ	: Get multi suffix integer from keyboard
;------------------------------------------------
;ARG	: -
;------------------------------------------------
;NOTE	: Expected Suffix- b(binary), d(decimal)
;		: h(hex), o(octal). d is optional
;		: Variable must be of type DQ
;		: Digits entered must be in valid format
;RETN	: Value in RAX
;------------------------------------------------
getint:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16
	push	rcx
	push	rdx 
	push 	rbx 
	push	rdi 
	push	rsi 
	xor		rax,rax
	xor 	rdi,rdi    		
	call	getch
	cmp		al,'-'
	jne 	.norm
	mov		byte[rbp-2],1 	;flag
.begin:
	call	getch
.norm:
	cmp		al,0ah
	jz 		.select
	push	rax
	inc 	rdi
	jmp 	.begin
.select:
	pop 	rax
	cmp 	al,'h'
	je 		.hexadecimal
	cmp		al,'H'
	je 		.hexadecimal
	cmp 	al,'b'
	je 		.binary
	cmp 	al,'B'
	je 		.binary
	cmp 	al,'o'
	je 		.octal
	cmp 	al,'O'
	je 		.octal
	cmp 	al,'d'
	je 		.decimal
	cmp 	al,'D'
	je 		.decimal
	push 	rax     		;no suffix, assume decimal
	inc 	rdi      		;re-adjust loop
.decimal:   
	xor 	rsi,rsi			;Accumulator
	pop 	rax
	sub 	al,30h
	add 	rsi,rax
	mov 	ecx,10
	mov 	ebx,ecx
	dec 	rdi
	jmp 	.translate
.hexadecimal:
	xor 	rsi,rsi
	pop 	rax
	cmp 	al,'a'
	jae 	.smalls
	cmp 	al,'A'
	jae 	.bigs
	jmp 	.proceed
.bigs:
	cmp 	al,'F'
	ja 		.big
.big:
	sub 	al,7h
	jmp 	.proceed
.smalls:
	cmp 	al,'f'
	ja 		.proceed
.small:
	sub 	al,27h
.proceed:		
	sub 	al,30h
	add 	rsi,rax
	mov 	ecx,16
	mov 	ebx,ecx
	dec 	rdi
	jmp 	.translate
.octal:
	xor 	rsi,rsi
	pop 	rax
	sub 	al,30h
	add 	rsi,rax
	mov 	ecx,8
	mov 	ebx,ecx
	dec 	rdi
	jmp 	.translate
.binary:    
	xor 	rsi,rsi
	pop 	rax
	sub 	al,30h
	add 	rsi,rax
	mov 	ecx,2
	mov 	ebx,ecx
	dec 	rdi
	jmp 	.translate
.translate:
	dec 	rdi
	jz 		.exit
	pop 	rax
	cmp 	rbx,16
	jne 	.proceed1
	cmp 	al,'a'
	jae 	.Smalls
	cmp 	al,'A'
	jae 	.Bigs
	jmp 	.proceed1
.Bigs:
	cmp 	al,'F'
	ja 		.Big
.Big:
	sub 	al,7h
	jmp 	.proceed1
.Smalls:
	cmp 	al,'f'
	ja 		.proceed1
.Small:
	sub 	al,27h
.proceed1:	
	sub 	al,30h 
	mul 	rcx
	add 	rsi,rax
	mov 	rax,rbx
	mul 	rcx
	mov 	rcx,rax
	jmp 	.translate
.exit:      
	cmp 	byte[rbp-2],1
	jne		.out
	neg 	rsi
.out:
	mov 	rax,rsi
	pop 	rsi 
	pop 	rdi 
	pop 	rbx
	pop		rdx
	pop 	rcx 
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#22	: getdbl(0)/XMM0
;OBJ	: Get double-precision from stdin
;------------------------------------------------
;ARG	: -
;------------------------------------------------
;NOTE	: Variable must be initialized to fp (0.0)
;		: Variable must be of type DQ
;		: Does not take exponential format
;		: Must use fp format for input (x.x)
;RETN	: Double precision in XMM0
;------------------------------------------------
getdbl:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16*9
	push	rcx 
	push	rbx 
	push	rdx 
	push	r11					;preserve this
	lea		rcx,[rbp-138]
	fsave	[rcx]
	mov 	rcx,3FF0000000000000h			
	mov 	qword[rbp-12],rcx
	mov 	dword[rbp-4],0x41200000
	xor 	rbx,rbx
.again:
	call	getch
	cmp		al,0ah
	je 		.done
	cmp		al,'-'
	jne		.ok
	mov		byte[rbp-29],1
	jmp		.again
.ok:
	cmp		al,'.'
	jne 	.point
	mov 	rdx,rbx
	jmp 	.again
.point:
	sub		al,30h
	push	rax
	inc		rbx
	jmp 	.again
.done:
	pop 	qword[rbp-28]	
	finit
	fild 	qword[rbp-28]	
	fstp 	qword[rbp-20]	
	mov		rcx,rbx
	dec		rcx
.rr:						
	finit
	fld 	qword[rbp-12]	
	fmul 	dword[rbp-4]
	fst 	qword[rbp-12]
	pop 	qword[rbp-28]	
	fild 	qword[rbp-28]	
	fmul 	st0,st1
	fld 	qword[rbp-20]	
	fadd 	st0,st1			 
	fstp 	qword[rbp-20]	
	loop 	.rr
	mov 	rcx,rbx
	sub 	rcx,rdx
	finit
	fld 	qword[rbp-20]			
.d:		
	fdiv 	dword[rbp-4]	
	loop 	.d
.quit:
	fstp 	qword[rbp-20]		
	mov 	rax,qword[rbp-20] 	
	cmp 	byte[rbp-29],1		
	jne 	.out
	bts 	rax,63
.out:			
	lea		rcx,[rbp-138]
	frstor	[rcx]
	movq	xmm0,rax
	pop		r11 
	pop 	rdx 
	pop 	rbx 
	pop 	rcx 
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#23	: getflt/xmm0
;OBJ	: Get single-precision from stdin
;------------------------------------------------
;ARG	: -
;------------------------------------------------
;NOTE	: Variable must be initialized to fp (0.0)
;		: Does not take exponential format
;		: Must use fp format for input (x.x)
;RETN	: Single precision in xmm0 (use MOVD)
;------------------------------------------------
getflt:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16*9
	push	rcx 
	push	rbx 
	push	rdx 
	push	rsi 
	push	rdi
	lea		rsi,[rbp-138]
	fsave	[rsi]
	mov 	dword[rbp-12],0x3f800000
	mov 	dword[rbp-4],0x41200000
	xor 	rbx,rbx
	xor		rsi,rsi
.again:
	call	getch
	cmp		al,0ah
	je 		.done
	cmp		al,'-'
	jne		.ok
	mov		edi,1
	jmp		.again
.ok:
	cmp		al,'.'
	jne 	.point
	mov 	edx,ebx
	jmp 	.again
.point:
	sub		al,30h
	push	rax
	inc		rbx
	jmp 	.again
.done:
	pop 	qword[rbp-28]	
	finit
	fild 	dword[rbp-28]	
	fstp 	dword[rbp-20]	
	mov		ecx,ebx
	dec		ecx
.rr:		
	finit
	fld 	dword[rbp-12]	
	fmul 	dword[rbp-4]
	fst 	dword[rbp-12]
	pop 	qword[rbp-28]	
	fild 	dword[rbp-28]	
	fmul 	st0,st1
	fld 	dword[rbp-20]	
	fadd 	st0,st1			 
	fstp 	dword[rbp-20]	
	loop 	.rr
	mov 	ecx,ebx
	sub 	ecx,edx
	finit
	fld 	dword[rbp-20]			
.d:		
	fdiv 	dword[rbp-4]	
	loop 	.d
.quit:
	fstp 	dword[rbp-20]		
	mov 	eax,dword[rbp-20] 	
	cmp 	edi,1		
	jne 	.out
	bts 	eax,31
.out:			
	lea		rsi,[rbp-138]
	frstor	[rsi]
	movd	xmm0,eax ;alt. return
	pop		rdi
	pop 	rsi 
	pop 	rdx 
	pop 	rbx 
	pop 	rcx 
	mov 	rsp,rbp
	pop 	rbp
	ret
;--------------------------------
;#24	: fpu_stack(0)
;OBJ	: Display FPU stack.
;--------------------------------
;ARG	: - 
;--------------------------------
;NOTE	: Use FCLEX where appropriate
;		: FINIT will reset the Stack
;RETN	: -
;--------------------------------
fpu_stack:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16*2
	push 	rdx 
	push	rdi 
	push	rax 
	push	rsi
	mov 	dword[rbp-24],'...<'
	mov 	dword[rbp-20],'inf>'
	mov 	dword[rbp-16],'<NAN'
	mov 	dword[rbp-12],'><ba'
	mov 	word[rbp-8],'d>'
	mov 	byte[rbp-6],0
	mov 	dword[rbp-5],'ST::'
	mov 	byte[rbp-1],' '
	xor 	rdx,rdx
	call 	newline 
.again: 
	fst 	qword[rbp-32]
	mov 	esi,2
	lea 	rdi,[rbp-5]
	call	prtstr
	add 	dl,30h
	mov 	byte[rbp-6],dl
	lea 	rdi,[rbp-6]
	call	prtchar
	mov 	esi,2
	lea 	rdi,[rbp-2]
	call	prtstr
	sub 	dl,30h
	;----------------------
	xor 	rax,rax
	fxam
	fstsw 	ax
	and 	eax,4500h ;Mask C3, C2 and C0
	cmp 	eax,4100h
	jne 	.nxt1
	mov 	esi,3
	lea 	rdi,[rbp-24]
	call	prtstr
	jmp 	.go
.nxt1:
	cmp 	eax,500h
	jne 	.nxt2
	mov 	esi,5
	lea 	rdi,[rbp-21]
	call	prtstr
	jmp 	.go
.nxt2:
	cmp 	eax,100h
	jne 	.nxt3
	mov 	esi,5
	lea 	rdi,[rbp-16]
	call	prtstr
	jmp 	.go
.nxt3:	
	cmp 	eax,0
	jne 	.nxt4
	mov 	esi,5
	lea 	rdi,[rbp-11]
	call	prtstr
	jmp 	.go
	;----------------------
.nxt4:
	fclex
	movq	xmm0,[rbp-32]
	call 	prtdbl
.go:	
	call 	newline
	cmp 	rdx,7
	je 		.out
	fincstp    		;rotate stack
	inc 	rdx
	jmp 	.again
.out:	
	fincstp
	pop 	rsi 
	pop 	rax 
	pop 	rdi 
	pop 	rdx
	mov 	rsp,rbp
	pop 	rbp
	ret
;--------------------------------
;#25	: fpu_sflag(0)
;OBJ	: Display FPU Status Flag
;--------------------------------
;ARG	: - 
;--------------------------------
;NOTE	: -
;RETN	: -
;--------------------------------
fpu_sflag:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16*4
	push 	rax 
	push	rsi 
	push	rdi 
	push	rdx 
	push	rcx
	call	newline
	mov 	rax,'B C3 TP '
	mov 	qword[rbp-50],rax
	mov 	rax,'TP TP C2'
	mov 	qword[rbp-42],rax
	mov 	rax,' C1 C0 I'
	mov 	qword[rbp-34],rax
	mov 	rax,'R SF  P '
	mov 	qword[rbp-26],rax
	mov 	rax,' U  O  Z'
	mov 	qword[rbp-18],rax
	mov 	rax,'  D  I01'
	mov 	qword[rbp-10],rax
	mov 	word[rbp-2],'  '
	xor 	rax,rax
	fstsw 	ax
	fwait
	push 	rax
.done:	
	mov 	esi,46
	lea 	rdi,[rbp-50]
	call	prtstr
	call 	newline
	mov 	rcx,15
	pop 	rdx
.go1:	
	bt  	rdx,rcx
	jc  	.one
	mov 	esi,1
	lea 	rdi,[rbp-4]
	call	prtstr
.y:	
	test 	rcx,rcx
	jz  	.out
	dec		rcx
	mov 	esi,2
	lea 	rdi,[rbp-2]
	call	prtstr
	jmp		.go1
.one:	
	mov 	esi,1
	lea 	rdi,[rbp-3]
	call	prtstr
	jmp		.y
.out:	
	mov		al,'='
	call	prtchr
	mov 	rdi,rdx
	call 	prthex
	call 	newline
	pop 	rcx 
	pop 	rdx
	pop 	rdi 
	pop 	rsi 
	pop 	rax 
	mov 	rsp,rbp
	pop 	rbp
	ret
;--------------------------------
;#26	: fpu_cflag(0)
;OBJ	: Display FPU Control Flag
;--------------------------------
;ARG	: - 
;--------------------------------
;NOTE	: -
;RETN	: -
;--------------------------------
fpu_cflag:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16*4
	push 	rax 
	push	rsi 
	push	rdi 
	push	rdx 
	push	rcx
	mov 	rax,'        '
	mov 	qword[rbp-52],rax
	mov 	rax,'IC RC RC'
	mov 	qword[rbp-44],rax
	mov 	rax,' PC PC I'
	mov 	qword[rbp-36],rax
	mov 	rax,'EM   PM '
	mov 	qword[rbp-28],rax
	mov 	rax,'UM OM ZM'
	mov 	qword[rbp-20],rax
	mov 	rax,' DM IM01'
	mov 	qword[rbp-12],rax
	mov 	word[rbp-4],'  '
	mov		word[rbp-2],0
	fstcw 	word[rbp-2]
	call	newline
.done:
	mov 	esi,46
	lea 	rdi,[rbp-52]
	call	prtstr
	call 	newline
	mov 	rcx,15
	xor 	rdx,rdx
	mov 	dx,word[rbp-2]
.go1:	
	bt  	rdx,rcx
	jc  	.one
	lea 	rdi,[rbp-6]
	call	prtchar
.y:	
	test 	rcx,rcx
	jz  	.out
	dec		rcx
	mov		esi,2
	lea		rdi,[rbp-4]
	call	prtstr
	jmp 	.go1
.one:	
	lea 	rdi,[rbp-5]
	call	prtchar
	jmp 	.y
.out:
	mov		al,'='
	call	prtchr
	mov		rdi,rdx
	call 	prthex
	call 	newline
	pop 	rcx 
	pop 	rdx 
	pop 	rdi 
	pop 	rsi 
	pop 	rax
	mov		rsp,rbp
	pop		rbp
	ret
;----------------------------------------
;#27	: fpu_reg(1)
;OBJ	: Display one FPU stack register
;----------------------------------------
;RDI	: Stack number to display (0-7)
;	    > reg64,[dq],imm32
;----------------------------------------
;NOTE	: -
;RETN	: -
;----------------------------------------
fpu_reg: 
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16
	push 	rcx 
	push	rax
	push	rdi
	xor 	rcx,rcx
	mov 	rax,rdi
	test 	rax,rax
	js 		.done
	cmp 	rax,7
	ja 		.done
.again:
	cmp 	rcx,rax
	je 		.ok
	fincstp
	inc 	rcx
	cmp 	rcx,7
	je 		.done
	jmp 	.again
.ok:
	fst 	qword[rbp-8]
	fxam
	fstsw 	ax
	and 	eax,4500h
	cmp 	eax,4000h
	jne 	.next
	mov		qword[rbp-8],0
	jmp		.nxt
.next:	
	cmp 	eax,4100h
	je 		.done
	cmp 	eax,500h
	je 		.done
	cmp 	eax,100h
	je 		.done
	cmp 	eax,0
	je 		.done
.nxt:
	movq	xmm0,[rbp-8]
	call 	prtdbl
.done:
	pop		rdi
	pop 	rax 
	pop 	rcx
	mov 	rsp,rbp
	pop 	rbp
	ret
;---------------------------------------------
;#28	: fpu_copy(1)/XMM0
;OBJ	: Copy a FPU register
;---------------------------------------------
;RDI	: Stack number to copy (0-7)
;	    > reg64,[dq],imm
;---------------------------------------------
;NOTE	: Variable should be initialized to 0.0
;		: Variable should be of type DQ
;RETN	: Copied value in XMM0
;---------------------------------------------
fpu_copy:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16
	push	rax
	push	rsi
	push	rdi
	xor 	eax,eax
.go:
	cmp 	rax,rdi
	jne 	.a
	fst 	qword[rbp-8]
.a:	
	fincstp
	inc 	rax
	cmp 	rax,8
	je 		.done
	jmp 	.go
.done:	
	movq	xmm0,[rbp-8]
	pop		rdi
	pop		rsi
	pop		rax	
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#29	: str2int(1)/rax
;OBJ	: Convert 0-terminated string to integer
;------------------------------------------------
;RDI 	: The address of the zero-ended string
;		> add64, reg64
;------------------------------------------------
;NOTE	: Expected Suffix- b(binary), d(decimal)
;		: h(hex), o(octal). Decimal is optional
;		: String must be of type DB
;		: Digits must be valid
;RETN	: Value in RAX 
;------------------------------------------------
str2int:
	push 	rcx 
	push 	rbx 
	push	r8 
	push	r9 
	push	rdx
	push	r15
	push	rdi
	push	rsi
	xor		rax,rax
	xor 	r8,r8    		
	mov		rsi,rdi
	lodsb
	cmp		al,'-'
	jne 	.norm
	mov		r15b,1 	;sign flag
.begin: 
	lodsb
.norm:
	cmp		al,0
	jz 		.select
	push	rax
	inc 	r8
	jmp 	.begin
.select:
	pop 	rax
	cmp 	al,'h'
	je 		.hexadecimal
	cmp		al,'H'
	je 		.hexadecimal
	cmp 	al,'b'
	je 		.binary
	cmp 	al,'B'
	je 		.binary
	cmp 	al,'o'
	je 		.octal
	cmp 	al,'O'
	je 		.octal
	cmp 	al,'d'
	je 		.decimal
	cmp 	al,'D'
	je 		.decimal
	push 	rax  	;no suffix, assume decimal
	inc 	r8   	;re-adjust loop
.decimal:   
	xor 	r9,r9
	pop 	rax
	sub 	al,30h
	add 	r9,rax
	mov 	ecx,10
	mov 	ebx,ecx
	dec 	r8
	jmp 	.translate
.hexadecimal:
	xor 	r9,r9
	pop 	rax
	cmp 	al,'a'
	jae 	.smalls
	cmp 	al,'A'
	jae 	.bigs
	jmp 	.proceed
.bigs:
	cmp 	al,'F'
	ja 		.big
.big:
	sub 	al,7h
	jmp 	.proceed
.smalls:
	cmp 	al,'f'
	ja 		.proceed
.small:
	sub 	al,27h
.proceed:		
	sub 	al,30h
	add 	r9,rax
	mov 	ecx,16
	mov 	ebx,ecx
	dec 	r8
	jmp 	.translate
.octal:
	xor 	r9,r9
	pop 	rax
	sub 	al,30h
	add 	r9,rax
	mov 	ecx,8
	mov 	ebx,ecx
	dec 	r8
	jmp 	.translate
.binary:    
	xor 	r9,r9
	pop 	rax
	sub 	al,30h
	add 	r9,rax
	mov 	ecx,2
	mov 	ebx,ecx
	dec 	r8
	jmp 	.translate
.translate:
	dec 	r8
	jz 		.exit
	pop 	rax
	cmp 	rbx,16
	jne 	.proceed1
	cmp 	al,'a'
	jae 	.Smalls
	cmp 	al,'A'
	jae 	.Bigs
	jmp 	.proceed1
.Bigs:
	cmp 	al,'F'
	ja 		.Big
.Big:
	sub 	al,7h
	jmp 	.proceed1
.Smalls:
	cmp 	al,'f'
	ja 		.proceed1
.Small:
	sub 	al,27h
.proceed1:	
	sub 	al,30h 
	mul 	rcx
	add 	r9,rax
	mov 	rax,rbx
	mul 	rcx
	mov 	rcx,rax
	jmp 	.translate
.exit:      
	cmp 	r15b,1
	jne		.out
	neg 	r9
.out:
	mov 	rax,r9
	pop		rsi
	pop		rdi
	pop		r15
	pop		rdx
	pop 	r9 
	pop 	r8
	pop 	rbx
	pop 	rcx
	ret
;------------------------------------------------
;#30	: str2dbl(1)/XMM0
;OBJ	: Convert double-precision string
;------------------------------------------------
;RDI	: Address of a 0-terminated string
;		> add64, reg64
;------------------------------------------------
;NOTE	: -
;RETN	: Double precision in XMM0
;------------------------------------------------
str2dbl:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16*9
	push	rcx 
	push	r8 
	push	r9 
	push	r10 
	push	r11				;preserve this
	push	rdi
	push	rsi
	lea		r10,[rbp-138]
	fsave	[r10]
	mov 	r10,3FF0000000000000h			
	mov 	r8d,41200000h
	mov 	qword[rbp-12],r10
	mov 	dword[rbp-4],r8d
	xor 	r8,r8
	xor		rax,rax
	mov		rsi,rdi
.again:
	lodsb
	cmp		al,0
	je 		.done
	cmp		al,'-'
	jne		.ok
	mov		byte[rbp-29],1
	jmp		.again
.ok:
	cmp		al,'.'
	jne 	.point
	mov 	r9,r8
	jmp 	.again
.point:
	sub		al,30h
	push	rax
	inc		r8
	jmp 	.again
.done:
	pop 	qword[rbp-28]	
	finit
	fild 	qword[rbp-28]	
	fstp 	qword[rbp-20]	
	mov		rcx,r8
	dec		rcx
.rr:						
	finit
	fld 	qword[rbp-12]	
	fmul 	dword[rbp-4]
	fst 	qword[rbp-12]
	pop 	qword[rbp-28]	
	fild 	qword[rbp-28]	
	fmul 	st0,st1
	fld 	qword[rbp-20]	
	fadd 	st0,st1			 
	fstp 	qword[rbp-20]	
	loop 	.rr
	mov 	rcx,r8
	sub 	rcx,r9
	finit
	fld 	qword[rbp-20]			
.d:		
	fdiv 	dword[rbp-4]	
	loop 	.d
.quit:
	fstp 	qword[rbp-20]		
	mov 	rax,qword[rbp-20] 	
	cmp 	byte[rbp-29],1		
	jne 	.out
	bts 	rax,63
.out:			
	lea		r10,[rbp-138]
	frstor	[r10]
	movq	xmm0,rax
	pop		rsi
	pop		rdi
	pop		r11
	pop 	r10 
	pop 	r9
	pop 	r8 
	pop 	rcx 
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#31	: bconv(2)
;OBJ	: Convert and display integer (Unsigned)
;------------------------------------------------
;RSI	: Display base to use (2 to 36)
;	    > imm32,reg64,[dq]
;RDI	: Value to convert
;	    > imm32,reg64,[dq]
;------------------------------------------------
;NOTE	: Immediate value is limited to 32-bit
;RETN	: -
;------------------------------------------------
bconv:	
	push	rdi 
	push	rsi 
	push	rdx 
	push	rax 
	push	rcx
	push	rbx
	mov 	rbx,rsi 	
	mov 	rax,rdi 	
	xor 	rcx,rcx
.start:
	xor 	rdx,rdx
	div 	rbx
	push 	rdx
	test 	rax,rax
	jz 		.fine
	inc 	rcx
	jmp 	.start
.fine:	
	pop 	rax
	add 	al,30h
	cmp 	rax,39h
	jbe 	.num
	add 	al,7
.num:
	call	prtchr
	dec 	rcx
	js		.done
	jmp 	.fine
.done:	
	pop		rbx
	pop		rcx 
	pop 	rax 
	pop 	rdx 
	pop 	rsi
	pop 	rdi
	ret
;------------------------------------------------
;#32	: bitfield(3)
;OBJ	: Display a bitfield from a 64-bit data
;------------------------------------------------
;RDX	: lower bit
;	    > imm,reg64,[dq]
;RSI	: higher bit
;	    > imm,reg64,[dq]
;RDI	: Value to be extracted from
;	    > imm,reg64,[dq]
;------------------------------------------------
;NOTE	: Display bit range
;RETN	: -
;------------------------------------------------
bitfield:
	push	rdi
	push	rsi 
	push	rdx 
	push 	rax 
.no:
	mov 	al,'0'
	bt 		rdi,rsi
	jnc 	.g
	mov		al,'1'
.g:	
	call	prtchr
	cmp 	rsi,rdx
	je 		.done
	dec 	rsi
	jmp 	.no
.done:
	pop 	rax 
	pop 	rdx 
	pop 	rsi 
	pop 	rdi 
	ret
;--------------------------------------------
;#33	: powb10(2)/RAX
;OBJ	: Calculate 64-bit power (unsigned)
;--------------------------------------------
;RSI	: Exponent/power
;	    > reg64,[dq],imm32
;RDI	: Base
;	    > reg64,[dq],imm32
;--------------------------------------------
;NOTE	: Variable must be of type DQ
;RETN	: Result in RAX
;		: 0 if overflow
;--------------------------------------------
powb10:
	push	rsi 
	push	rdi
	push	rcx 
	mov 	rcx,rdi
	mov 	rax,rcx
	cmp		rsi,1
	jz		.done
	cmp		rsi,0
	jnz		.nxt
	mov		rax,1
	jmp		.done
.nxt:
	test	rsi,rsi
	jnz		.again
	mov		rax,1
	jmp 	.done
.again:
	mul 	rcx
	jo		.overflow
	dec 	rsi
	cmp 	rsi,1
	je 		.done
	jmp 	.again
.overflow:
	xor		rax,rax
.done:	
	pop 	rcx 
	pop		rdi
	pop 	rsi 
	ret
;---------------------------------------
;#34	: pow(2)/xmm0
;OBJ	: Get FP power value
;---------------------------------------
;RDI	: Power (unsigned integer)
;		> reg64, imm, [dq]
;XMMO	: The value (base). In FP format
;		> [dq],reg64
;---------------------------------------
;NOTE	: RDI must be in integer format
;		: xmm0 must be in FP format
;RETN	: The value in xmm0
;---------------------------------------
pow:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16*8
	push	rcx
	lea		rcx,[rbp-124]
	fsave	[rcx]
	finit
	movq 	[rbp-16],xmm0
	fld 	qword[rbp-16]
	mov		rax,qword[rbp-16]
	test	rax,rax
	jns		.nxt
	mov		al,1
.nxt:	
	mov 	rcx,rdi
	cmp		rcx,1
	jz		.done
	cmp		rcx,0
	jnz		.ok
	fld1
	jmp		.done
.ok:	
	dec 	rcx
.go:
	fmul 	qword [rbp-16]	
	loop 	.go
.done:
	fstp 	qword[rbp-8]
	cmp		al,1
	jne		.out
	bts		qword[rbp-8],63
.out:	
	movq 	xmm0,[rbp-8]
	lea		rcx,[rbp-124]
	frstor	[rcx]
	pop		rcx
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#35	: sqroot(1)/XMM0
;OBJ	: Get square root of a given value
;------------------------------------------------
;XMM0	: Value to be squared
;	    > reg64, [dq] (use movq)
;------------------------------------------------
;NOTE	: Variable should be initialize as FP (0.0)
;		: Immediate is of type FP
;		: Function will clear FPU stack
;RETN	: Square root value in XMM0
;------------------------------------------------
sqroot:
	push 	rbp
	mov 	rbp,rsp
	sub		rsp,16
	movq	[rbp-8],xmm0		
	finit
	fld 	qword[rbp-8]
	fabs
	fsqrt
	fstp 	qword[rbp-8]
	movq	xmm0,[rbp-8]
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#36	: rad2deg(1)/XMM0
;OBJ	: Convert Radian to Degree
;------------------------------------------------
;XMM0	: FP value in RADIAN
;	    > [dq],reg64 (use movq)
;------------------------------------------------
;NOTE	: Variable should be initialize as FP (0.0)
;		: Variable must be of type DQ
;		: Function will clear FPU stack
;RETN	: DEGREE value in XMM0 
;------------------------------------------------
rad2deg:
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16
	movq	[rbp-16],xmm0
	mov 	rax,404CA5DC1A47A9E3h
	mov 	[rbp-8],rax
	finit
	fld 	qword[rbp-16]
	fmul 	qword[rbp-8]
	fstp 	qword[rbp-16]
	movq	xmm0,[rbp-16]
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#37	: deg2rad(1)/XMM0
;OBJ	: Convert Degree to Radian
;------------------------------------------------
;XMM0	: FP value in RADIAN
;	    > [dq],reg64 (use movq)
;------------------------------------------------
;NOTE	: Variable should be initialize as FP (0.0)
;		: Variable must be of type DQ
;		: Function will clear FPU stack
;RETN	: RADIAN value in XMM0 
;------------------------------------------------
deg2rad: 
	push 	rbp
	mov 	rbp,rsp
	sub 	rsp,16
	movq	[rbp-16],xmm0
	mov 	rax,3F91DF46A1FAE711h
	mov		[rbp-8],rax
	finit
	fld		qword[rbp-16]
	fmul 	qword[rbp-8]
	fstp 	qword[rbp-16]
	movq	xmm0,[rbp-16]
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#38	: sine(1)/XMM0
;OBJ	: Get sine value
;------------------------------------------------
;XMM0	: FP value in RADIAN
;	    > [dq],reg64 (use movq)
;------------------------------------------------
;NOTE	: Variable should be initialize as FP (0.0)
;		: Variable must be of type DQ
;		: Function will clear FPU stack
;RETN	: Sine value in XMM0 
;------------------------------------------------
sine:
	push 	rbp
	mov 	rbp,rsp
	sub		rsp,16
	movq	[rbp-8],xmm0
	finit
	fld 	qword[rbp-8]
	fsin
	fstp 	qword[rbp-8]	  
	movq	xmm0,[rbp-8]
	mov 	rsp,rbp
	pop 	rbp	
	ret
;------------------------------------------------
;#39	: tangent(1)/XMM0
;OBJ	: Get tangent
;------------------------------------------------
;XMM0	: FP value in RADIAN
;	    > [dq],reg64 (use movq)
;------------------------------------------------
;NOTE	: Variable should be initialize as FP (0.0)
;		: Variable must be of type DQ
;		: Function will clear FPU stack
;RETN	: Tangent value in XMM0 
;------------------------------------------------
tangent:
	push 	rbp
	mov 	rbp,rsp
	sub		rsp,16
	movq	[rbp-8],xmm0
	finit
	fld 	qword[rbp-8]
	fptan
	fxch
	fstp 	qword[rbp-8]
	movq	xmm0,[rbp-8]
	mov 	rsp,rbp
	pop 	rbp
	ret
;------------------------------------------------
;#40	: cosine(1)/XMM0
;OBJ	: Get cosine value
;------------------------------------------------
;XMM0	: FP value in RADIAN
;	    > [dq],reg64 (use movq)
;------------------------------------------------
;NOTE	: Variable should be initialize as FP (0.0)
;		: Variable must be of type DQ
;		: Function will clear FPU stack
;RETN	: Cosine value in XMM0 
;------------------------------------------------
cosine:
	push 	rbp
	mov 	rbp,rsp
	sub		rsp,16
	movq	[rbp-8],xmm0
	finit
	fld 	qword[rbp-8]
	fcos
	fstp 	qword[rbp-8]
	movq	xmm0,[rbp-8]
	mov 	rsp,rbp
	pop 	rbp	
	ret
;------------------------------------------------
;#41	: atangent(1)/XMM0
;OBJ	: Get arc-tangent
;------------------------------------------------
;XMM0	: FP value in RADIAN
;	    > [dq],reg64 (use movq)
;------------------------------------------------
;NOTE	: Variable should be initialize as FP (0.0)
;		: Variable must be of type DQ
;		: Function will clear FPU stack
;RETN	: arc Tangent value in XMM0 
;------------------------------------------------
atangent:
	push 	rbp
	mov 	rbp,rsp
	sub		rsp,16
	movq	[rbp-8],xmm0
	finit
	fld 	qword[rbp-8]
	fld1
	fpatan
	fstp 	qword[rbp-8]
	movq	xmm0,[rbp-8]
	mov 	rsp,rbp
	pop 	rbp
	ret
;--------------------------------
;#42	: prtxmm(1)
;OBJ	: Display XMM register
;--------------------------------
;RDI	: Register number to display
;		> reg,imm,[dq]
;--------------------------------
;NOTE	: Display 64-digit Hex format
;RETN	: -
;--------------------------------
prtxmm:
	push	rbp
	mov		rbp,rsp
	sub		rsp,16
	push	rdi
	push	rax
	cmp		rdi,0
	jz		.xmm0
	cmp		rdi,1
	jz		.xmm1
	cmp		rdi,2
	jz		.xmm2
	cmp		rdi,3
	jz		.xmm3
	cmp		rdi,4
	jz		.xmm4
	cmp		rdi,5
	jz		.xmm5
	cmp		rdi,6
	jz		.xmm6
	cmp		rdi,7
	jz		.xmm7
	cmp		rdi,8
	jz		.xmm8
	cmp		rdi,9
	jz		.xmm9
	cmp		rdi,10
	jz		.xmm10
	cmp		rdi,11
	jz		.xmm11
	cmp		rdi,12
	jz		.xmm12
	cmp		rdi,13
	jz		.xmm13
	cmp		rdi,14
	jz		.xmm14
	cmp		rdi,15
	jz		.xmm15
.err:
	mov		al,'#'
	call	prtchr
	jmp		.done	
.xmm0:
	movdqu	[rbp-16],xmm0
	jmp		.disp
.xmm1:
	movdqu	[rbp-16],xmm1
	jmp		.disp
.xmm2:
	movdqu	[rbp-16],xmm2
	jmp		.disp
.xmm3:
	movdqu	[rbp-16],xmm3
	jmp		.disp
.xmm4:
	movdqu	[rbp-16],xmm4
	jmp		.disp
.xmm5:
	movdqu	[rbp-16],xmm5
	jmp		.disp
.xmm6:
	movdqu	[rbp-16],xmm6
	jmp		.disp
.xmm7:
	movdqu	[rbp-16],xmm7
	jmp		.disp
.xmm8:
	movdqu	[rbp-16],xmm8
	jmp		.disp
.xmm9:
	movdqu	[rbp-16],xmm9
	jmp		.disp
.xmm10:
	movdqu	[rbp-16],xmm10
	jmp		.disp
.xmm11:
	movdqu	[rbp-16],xmm11
	jmp		.disp
.xmm12:
	movdqu	[rbp-16],xmm12
	jmp		.disp
.xmm13:
	movdqu	[rbp-16],xmm13
	jmp		.disp
.xmm14:
	movdqu	[rbp-16],xmm14
	jmp		.disp
.xmm15:
	movdqu	[rbp-16],xmm15
	jmp		.disp
	jmp		.done
.disp:
	mov		rdi,qword[rbp-8]
	call	prtreg
	mov		al,' '
	call	prtchr
	mov		rdi,qword[rbp-16]
	call	prtreg
.done:
	pop		rax
	pop		rdi
	mov		rsp,rbp
	pop		rbp
	ret	
;--------------------------------
;#43	: dumpxmm
;OBJ	: Dump XMM registers
;--------------------------------
;ARG	: -
;--------------------------------
;NOTE	: Display Hex format
;RETN	: -
;--------------------------------
dumpxmm:
	push 	rbp
	mov		rbp,rsp
	sub		rsp,16
	push	rax
	push	rcx
	push	rdi
	push	rsi
	mov		rax,0
	mov		rcx,16
.again:
	mov		dword[rbp-3],"XMM"
	lea		rdi,[rbp-3]
	mov		rsi,3
	call	prtstr
	mov		rsi,0
	mov		rdi,rax
	call	prtdec
	push	rax
	cmp		rax,9
	ja		.nope
	mov		al,' '
	call	prtchr
.nope:	
	mov		al,':'
	call	prtchr
	pop		rax
	mov		rdi,rax
	call	prtxmm
	inc		rax
	call	newline
	loop	.again
.done:	
	pop		rsi
	pop		rdi
	pop		rcx
	pop		rax
	mov		rsp,rbp
	pop		rbp
	ret
;--------------------------------
;#44	: dumpfxmm(1)
;OBJ	: Dump XMMs in floating format
;--------------------------------
;RDI	: Type of display:
;		:      0 - four floats format
;		:      1 - Two double format
;		> imm,reg,[dq]
;--------------------------------
;NOTE	: Display 4 floats or 2 doubles
;RETN	: -
;--------------------------------
dumpfxmm:
	push	rbp
	mov		rbp,rsp
	sub		rsp,16
	push	rax
	push	rsi
	push	rdi
	push	rbx
	push	rdx
	mov		rbx,rdi
	mov		rdx,0
	mov		dword[rbp-3],"XMM"
.again:
	mov		rsi,3
	lea		rdi,[rbp-3]
	call	prtstr
	mov		rdi,rdx
	call	prtdecu
	cmp		rdx,9
	ja		.nope
	mov		al,' '
	call	prtchr
.nope:
	mov		al,':'
	call	prtchr
	mov		al,' '
	call	prtchr
	cmp		rbx,0
	jz		.dispfloat
	call	prtxmmq
.back:
	inc		rdx
	cmp		rdx,16
	je		.done
	call	newline
	jmp		.again
.dispfloat:
	call	prtxmmf
	jmp		.back
.done:	
	pop		rdx
	pop		rbx
	pop		rdi
	pop		rsi
	pop		rax
	mov		rsp,rbp
	pop		rbp
	ret
;--------------------------------
;#45	: prtxmmf(1)
;OBJ	: Display XMM register (4 floats)
;--------------------------------
;RDI	: Register number to display
;		> reg,imm,[dq]
;--------------------------------
;NOTE	: Display four 32-bit floats
;RETN	: -
;--------------------------------
prtxmmf:
	push	rbp
	mov		rbp,rsp
	sub		rsp,32
	push	rax
	push	rdi
	push	rcx
	movdqu	[rbp-32],xmm0
	cmp		rdi,0
	jz		.xmm0
	cmp		rdi,1
	jz		.xmm1
	cmp		rdi,2
	jz		.xmm2
	cmp		rdi,3
	jz		.xmm3
	cmp		rdi,4
	jz		.xmm4
	cmp		rdi,5
	jz		.xmm5
	cmp		rdi,6
	jz		.xmm6
	cmp		rdi,7
	jz		.xmm7
	cmp		rdi,8
	jz		.xmm8
	cmp		rdi,9
	jz		.xmm9
	cmp		rdi,10
	jz		.xmm10
	cmp		rdi,11
	jz		.xmm11
	cmp		rdi,12
	jz		.xmm12
	cmp		rdi,13
	jz		.xmm13
	cmp		rdi,14
	jz		.xmm14
	cmp		rdi,15
	jz		.xmm15
.err:
	mov		al,'#'
	call	prtchr
	jmp		.done
.xmm0:
	movdqu	[rbp-16],xmm0
	jmp		.disp
.xmm1:
	movdqu	[rbp-16],xmm1
	jmp		.disp
.xmm2:
	movdqu	[rbp-16],xmm2
	jmp		.disp
.xmm3:
	movdqu	[rbp-16],xmm3
	jmp		.disp
.xmm4:
	movdqu	[rbp-16],xmm4
	jmp		.disp
.xmm5:
	movdqu	[rbp-16],xmm5
	jmp		.disp
.xmm6:
	movdqu	[rbp-16],xmm6
	jmp		.disp
.xmm7:
	movdqu	[rbp-16],xmm7
	jmp		.disp
.xmm8:
	movdqu	[rbp-16],xmm8
	jmp		.disp
.xmm9:
	movdqu	[rbp-16],xmm9
	jmp		.disp
.xmm10:
	movdqu	[rbp-16],xmm10
	jmp		.disp
.xmm11:
	movdqu	[rbp-16],xmm11
	jmp		.disp
.xmm12:
	movdqu	[rbp-16],xmm12
	jmp		.disp
.xmm13:
	movdqu	[rbp-16],xmm13
	jmp		.disp
.xmm14:
	movdqu	[rbp-16],xmm14
	jmp		.disp
.xmm15:
	movdqu	[rbp-16],xmm15
.disp:
	movd	xmm0,dword[rbp-4]
	call	prtflt
	mov		al,'|'
	call	prtchr
	movd	xmm0,dword[rbp-8]
	call	prtflt
	mov		al,'|'
	call	prtchr
	movd	xmm0,dword[rbp-12]
	call	prtflt
	mov		al,'|'
	call	prtchr
	movd	xmm0,dword[rbp-16]
	call	prtflt
.done:
	movdqu	xmm0,[rbp-32]
	pop		rcx
	pop		rdi
	pop		rax
	mov		rsp,rbp
	pop		rbp
	ret
;--------------------------------
;#46	: prtxmmq(1)
;OBJ	: Display XMM register (2 doubles)
;--------------------------------
;RDI	: Register number to display
;		> reg,imm,[dq]
;--------------------------------
;NOTE	: Display two 64-bit doubles
;RETN	: -
;--------------------------------
prtxmmq:
	push	rbp
	mov		rbp,rsp
	sub		rsp,32
	push	rax
	push	rdi
	movdqu	[rbp-32],xmm0
	cmp		rdi,0
	jz		.xmm0
	cmp		rdi,1
	jz		.xmm1
	cmp		rdi,2
	jz		.xmm2
	cmp		rdi,3
	jz		.xmm3
	cmp		rdi,4
	jz		.xmm4
	cmp		rdi,5
	jz		.xmm5
	cmp		rdi,6
	jz		.xmm6
	cmp		rdi,7
	jz		.xmm7
	cmp		rdi,8
	jz		.xmm8
	cmp		rdi,9
	jz		.xmm9
	cmp		rdi,10
	jz		.xmm10
	cmp		rdi,11
	jz		.xmm11
	cmp		rdi,12
	jz		.xmm12
	cmp		rdi,13
	jz		.xmm13
	cmp		rdi,14
	jz		.xmm14
	cmp		rdi,15
	jz		.xmm15
.err:
	mov		al,'#'
	call	prtchr
	jmp		.done
.xmm0:
	movdqu	[rbp-16],xmm0
	jmp		.disp
.xmm1:
	movdqu	[rbp-16],xmm1
	jmp		.disp
.xmm2:
	movdqu	[rbp-16],xmm2
	jmp		.disp
.xmm3:
	movdqu	[rbp-16],xmm3
	jmp		.disp
.xmm4:
	movdqu	[rbp-16],xmm4
	jmp		.disp
.xmm5:
	movdqu	[rbp-16],xmm5
	jmp		.disp
.xmm6:
	movdqu	[rbp-16],xmm6
	jmp		.disp
.xmm7:
	movdqu	[rbp-16],xmm7
	jmp		.disp
.xmm8:
	movdqu	[rbp-16],xmm8
	jmp		.disp
.xmm9:
	movdqu	[rbp-16],xmm9
	jmp		.disp
.xmm10:
	movdqu	[rbp-16],xmm10
	jmp		.disp
.xmm11:
	movdqu	[rbp-16],xmm11
	jmp		.disp
.xmm12:
	movdqu	[rbp-16],xmm12
	jmp		.disp
.xmm13:
	movdqu	[rbp-16],xmm13
	jmp		.disp
.xmm14:
	movdqu	[rbp-16],xmm14
	jmp		.disp
.xmm15:
	movdqu	[rbp-16],xmm15
.disp:
	movq	xmm0,qword[rbp-8]
	call	prtdbl
	mov		al,'|'
	call	prtchr
	movq	xmm0,qword[rbp-16]
	call	prtdbl
.done:
	movdqu	xmm0,[rbp-32]
	pop		rdi
	pop		rax
	mov		rsp,rbp
	pop		rbp
	ret
;--------------------------------
;#47	: sse_flags(0)
;OBJ	: Display MXCSR register
;--------------------------------
;ARG	: -
;--------------------------------
;NOTE	: -
;RETN	: -
;--------------------------------
sse_flags:
	push	rbp
	mov		rbp,rsp
	sub		rsp,64
	push	rax
	push	rdx
	push	rcx
	push	rdi
	push	rsi
	stmxcsr dword[rbp-64]
	mov		dword[rbp-60],'  '
	mov		dword[rbp-48],'FZ R'
	mov		dword[rbp-44],'C RC'
	mov		dword[rbp-40],' PM '
	mov		dword[rbp-36],'UM O'
	mov		dword[rbp-32],'M ZM'
	mov		dword[rbp-28],' DM '
	mov		dword[rbp-24],'IM D'
	mov		dword[rbp-20],'Z PE'
	mov		dword[rbp-16],' UE '
	mov		dword[rbp-12],'OE Z'
	mov		dword[rbp-8],'E DE'
	mov		dword[rbp-4],' IE '
	call	newline
	mov		rsi,48
	lea		rdi,[rbp-48]
	call	prtstr
	call	newline
	mov		edx,0
	lea		rdi,[rbp-60]
	mov		esi,3
	mov		ecx,[rbp-64]
.again:
	mov		al,'0'
	bt		ecx,edx
	jnc		.ok
	mov		al,'1'
.ok:
	call	prtchr
	call	prtstr
	inc		edx
	cmp		edx,16
	jz		.done
	jmp		.again
.done:
	call	newline
	pop		rsi
	pop		rdi
	pop		rcx
	pop		rdx
	pop		rax
	mov		rsp,rbp
	pop		rbp
	ret
;----------------------------------------------
;#48	: rndigit(1)/RAX
;OBJ	: Get one random digit for normal bases
;----------------------------------------------
;RDI	: Base (8,10 or 16)
;		> [dq],reg64,imm32
;----------------------------------------------
;NOTE	: For base 8, base 10 or base 16
;RETN	: Random digit in RAX 
;----------------------------------------------
rndigit:
	push	rdx 
	push	rdi
	xor		rax,rax
.go:
	rdtsc
	shr		eax,1
	and 	eax,1111b
	cmp 	rax,rdi
	jae 	.go
	pop 	rdi 
	pop 	rdx
	ret
;------------------------------------------------
;#49	: chr_find(2)/RAX
;OBJ	: Find byte / position from a 0-ended string
;------------------------------------------------
;RSI	: Character to find
;	    > reg64,char imm8,qword[db]
;RDI	: Source string to look from
;	    > add64
;------------------------------------------------
;NOTE	: Will stop at first one found
;RETN	: Byte position in RAX. 0 if not found
;------------------------------------------------
chr_find:
	push	rdi
	push	rsi 
	push	rcx
	xor		rcx,rcx
	mov		rax,rsi
	cld
.again:	
	scasb
	jz 		.found
	cmp 	byte[rdi],0
	jz 		.notfound
	inc 	rcx
	jmp 	.again
.notfound:	
	mov		rcx,-1
.found:	
	mov		rax,rcx
	inc		rax
	pop		rcx 
	pop		rsi
	pop 	rdi
	ret
;------------------------------------------------
;#50	: chr_count(2)/RAX
;OBJ	: Count a character from a 0-ended string
;------------------------------------------------
;RSI	: Character to count
;	    > the char to count,reg,imm32,qword[db]
;RDI	: String's source
;	    > add64
;------------------------------------------------
;NOTE	: -
;RETN	: Count in RAX. 0 if none
;------------------------------------------------
chr_count:
	push	rdi
	push	rsi 
	push	rcx
	xor		rcx,rcx
	mov		rax,rsi
	cld
.again:	
	scasb
	jz 		.found
.next:
	cmp 	byte[rdi],0
	jz 		.end
	jmp 	.again
.found:	
	inc		rcx
	jmp		.next
.end:
	mov		rax,rcx
	pop		rcx
	pop		rsi 
	pop 	rdi
	ret
;---------------------------------------
;#51	: str_copy(3)
;OBJ	: Copy a string to another array
;---------------------------------------
;RDX	: Size of bytes to copy 
;	    > reg64,[dq],imm32
;RSI	: String's source address
;	    > add64
;RDI	: String's target address
;	    > add64
;------------------------------------------------
;NOTE	: Target must be of similar/fit the size to copy
;		: Arrays should be of type DB
;RETN	: Copied string at the sent address
;------------------------------------------------
str_copy:
	push	rcx
	push	rdx
	push	rsi
	push	rdi
	mov		rcx,rdx
	rep 	movsb
	pop		rdi
	pop		rsi
	pop		rdx
	pop		rcx
	ret
;------------------------------------------------
;#52	: str_length(1)/RAX
;OBJ	: Find length of a 0-ended string
;------------------------------------------------
;RDI	: String's source
;	    > add64
;------------------------------------------------
;NOTE	: -
;RETN	: size in RAX.
;------------------------------------------------
str_length:
	push	rdi 
	push	rcx
	mov 	rcx,-1
	mov 	al,0
	repne 	scasb
	mov 	rax,-2
	sub 	rax,rcx
	pop		rcx 
	pop 	rdi
	ret
;---------------------------------
;#53	:str_cmpz(2)/RAX
;OBJ	:Compare 0-ended strings 
;---------------------------------
;RSI	:String 1 location
;		> add64
;RDI	:String 2 location
;		> add64
;----------------------------------
;NOTE	:The two strings mus be 0-ended
;RETN	:RAX - 1 if Equal, 0 if not
;----------------------------------
str_cmpz:
	push 	rdi
	push 	rsi
	push 	rbx
	push 	rdx
	push 	rcx
	xor 	rax,rax
	xor 	rbx,rbx
	xor 	rdx,rdx
	xor 	rcx,rcx
.again:
	mov 	bl,byte[rsi+rcx]
	mov 	dl,byte[rdi+rcx]
	cmp 	dl,bl
	jne 	.out
	test 	bl,bl
	jz 		.done
	test 	dl,dl
	jz  	.done
	inc 	ecx
	jmp  	.again
.done:
	mov 	eax,1
.out:
	pop 	rcx
	pop 	rdx
	pop 	rbx
	pop 	rsi
	pop 	rdi
	ret
;---------------------------------
;#54	:str_cmps(3)/RAX
;OBJ	:Compare strings with size
;---------------------------------
;RDX 	:Size of bytes to compare
;		> imm32,[dq],reg
;RSI 	:String 1 location
;		> add64
;RDI 	:String 2 location
;		> add64
;----------------------------------
;NOTE	: -
;RETN	:RAX - 1 if Equal, 0 if not
;----------------------------------
str_cmps:
	push 	rdi
	push 	rsi
	push 	rcx
	mov 	rcx,rdx
	inc 	rcx
	xor 	rax,rax
	repe 	cmpsb
	jecxz 	.done
	jmp 	.out
.done:
	mov 	eax,1
.out:
	pop		rcx
	pop 	rsi
	pop 	rdi
	ret
;---------------------------------------
;#55	:str_toupper(1)
;OBJ	:Change 0-ended string to upper case
;---------------------------------------
;RDI 	:Address of the 0-ended string
;		> add64
;----------------------------------------
;NOTE	:-
;RETN	:The same string converted
;----------------------------------------
str_toupper:
	push 	rsi
	push 	rdi
	push 	rax
	cld
	mov 	rsi,rdi
.go:
	lodsb
	test 	al,al
	jz 		.done
	cmp 	al,' '
	je 		.nope
	and		al,0xdf ;btr ax,5
.nope:
	stosb
	jmp 	.go
.done:	
	pop		rax
	pop		rdi
	pop		rsi
	ret
;---------------------------------------
;#56	:str_tolower(1)
;OBJ	:Change 0-ended string to lower case
;---------------------------------------
;RDI 	:Address of the 0-ended string
;		> add64
;----------------------------------------
;NOTE	:-
;RETN	:The same string converted
;----------------------------------------
str_tolower:
	push 	rsi
	push 	rdi
	push 	rax
	cld
	mov 	rsi,rdi
.go:
	lodsb
	test 	al,al
	jz 		.done
	cmp 	al,' '
	je 		.nope
	or	 	al,0x20	;bts ax,5
.nope:
	stosb
	jmp 	.go
.done:	
	pop		rax
	pop		rdi
	pop		rsi
	ret
;---------------------------------------
;#57	:str_alternate(1)
;OBJ	:Alternate 0-ended string case
;---------------------------------------
;RDI 	:Address of the 0-ended string
;		> add64
;----------------------------------------
;NOTE	:-
;RETN	:The same string alternated
;----------------------------------------
str_alternate:
	push 	rsi
	push 	rdi
	push 	rax
	cld
	mov 	rsi,rdi
.go:
	lodsb
	test 	al,al
	jz 		.done
	cmp 	al,' '
	je 		.nope
	btc 	ax,5
.nope:
	stosb
	jmp 	.go
.done:	
	pop		rax
	pop		rdi
	pop		rsi
	ret
;---------------------------------------
;#58	:str_reverse(1)
;OBJ	:Alternate 0-ended string case
;---------------------------------------
;RDI 	:Address of the 0-ended string
;		> add64, reg64
;----------------------------------------
;NOTE	:-
;RETN	:The same string reversed
;----------------------------------------
str_reverse:
	push 	rsi
	push 	rdi
	push 	rax
	push	rcx
	mov 	rsi,rdi
	xor 	rcx,rcx
.again:
	lodsb
	cmp 	al,0
	jz 		.copy
	push 	rax
	inc 	rcx
	jmp 	.again
.copy:
	pop 	rax
	stosb
	loop 	.copy
.done:	
	pop		rcx
	pop		rax
	pop		rdi
	pop		rsi
	ret
;--------------------------------
;#59	: newline(0)
;OBJ	: Display/Print a newline
;--------------------------------
;ARG	: 0 
;--------------------------------
;NOTE	: 
;RETN	: 
;--------------------------------
newline:	
	push	rax
	mov		al,0ah
	call	prtchr
	pop		rax
	ret
;--------------------------------
;#60	: halt(0)
;OBJ	: Pause screen
;--------------------------------
;ARG	: 0 
;--------------------------------
;NOTE	: Hit Enter to continue
;RETN	: 
;--------------------------------
halt:
	push	rax
	call	getch
	pop		rax
	ret
;------------------------------------
;#61	: opsize(2)
;OBJ	: Display size between 2 labels
;------------------------------------
;RSI	: Label
;		> reg64,mem64
;RDI	: Label
;		> reg64,mem64
;------------------------------------
;NOTE	: -
;RETN	: -
;------------------------------------
opsize:
	push	rsi
	push	rdi
	sub		rdi,rsi
	jns		.ok
	neg		rdi
.ok:
	call	prtdecu
	pop		rdi
	pop		rsi
	ret
;--------------------------------
;#62	: exitp(0)
;OBJ	: Pause screen & exit to system.
;--------------------------------
;ARG	: 0 
;--------------------------------
;NOTE	: Put at the end of code
;RETN	: 
;--------------------------------
exitp:
	call 	getch
	call 	exit
	ret
;--------------------------------
;#63	: exit(0)
;OBJ	: Exit to system.
;--------------------------------
;ARG	: 0 
;--------------------------------
;NOTE	: Put at the end of code
;RETN	: 
;--------------------------------
exit:	
	xor 	edi,edi
	mov 	eax,60
	syscall
	ret
;-------------- END OF ROUTINES --------------
