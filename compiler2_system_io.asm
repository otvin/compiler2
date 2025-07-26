;----------
;
;   compiler2_system_io.asm
;	copyright 2020 M. "Fred" Fredericks
;	All Rights Reserved
;	io functions for compiler2
;
;----------

extern fputc
extern _PASCAL_OVERFLOW_ERROR

section .note.GNU-stack noalloc noexec nowrite progbits
section .text
    global _PASCAL_PRINTSTRINGTYPE



_PASCAL_PRINTSTRINGTYPE:						;Procedure printstringtype(s:array, k:integer)

;----------
;
;   _PASCAL_PRINTSTRINGTYPE
;       - writes the contents of a string-type (packed array of chars) or string literal to screen
;----------
;   RDI: Address of the string-type array to be printed
;   ESI: Length of the string-type array
;----------
; Returns: None
;----------

	PUSH RBP
	MOV RBP, RSP								;save stack pointer
	SUB RSP, 160								;allocate local storage
												; Parameter fileptr - [RBP-16]
												; Parameter s - [RBP-24]
												; Parameter k - [RBP-32]
												; Local Variable i - [RBP-8]
												; Local Variable _t0 - [RBP-40]
												; Local Variable _t1 - [RBP-48]
												; Local Variable _t2 - [RBP-56]
												; Local Variable _t3 - [RBP-64]
												; Local Variable _t4 - [RBP-72]
												; Local Variable _t5 - [RBP-80]
												; Local Variable _t6 - [RBP-88]
												; Local Variable _t7 - [RBP-96]
												; Local Variable _t8 - [RBP-104]
												; Local Variable _t9 - [RBP-112]
												; Local Variable _t10 - [RBP-120]
												; Local Variable _t11 - [RBP-128]
												; Local Variable _t12 - [RBP-136]
												; Local Variable _t13 - [RBP-144]
												; Local Variable _t14 - [RBP-152]
	mov [RBP-16], RDI							;Copy variable parameter fileptr to stack
	mov [RBP-24], RSI
	mov [RBP-32], EDX							;Copy parameter k to stack
; i := 1
	mov EAX, 1									;Move literal '1' into i
	mov [RBP-8], EAX
; while i <= k do
_PASCAL_PRINTSTRINGTYPE_TAC_L1_:
	mov eax,  [RBP-8]							;_T0 := i <= k
	mov r11d,  [RBP-32]
	cmp eax, r11d
	JLE _PASCAL_PRINTSTRINGTYPE_L0
	mov al, 0
	jmp _PASCAL_PRINTSTRINGTYPE_L1
_PASCAL_PRINTSTRINGTYPE_L0:
	mov al, 1
_PASCAL_PRINTSTRINGTYPE_L1:
	mov [RBP-40], al
	mov al, [RBP-40]
	test al,al
	jz _PASCAL_PRINTSTRINGTYPE_TAC_L2_
; if ord ( s [ i ] ) = 0 then
	mov RAX, [RBP-24]							;Move address of s into _T1
	mov [RBP-48], RAX
	mov eax,  [RBP-8]							;_T2 := i - 1
	mov r11d, 1
	sub eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-56], eax
	mov eax,  [RBP-56]							;_T3 := _T2 * 1
	mov r11d, 1
	imul eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-64], eax
	mov rax,  [RBP-48]							;_T4 := _T1 + _T3 with bounds check removed
	mov r11d,  [RBP-64]
	add rax, r11
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-72], rax
	mov r10, [RBP-72]							;Mov deref of _T4 to _T5
	mov AL, [r10]
	mov [RBP-80], AL
	mov R11B,  [RBP-80]							;parameter _T5 for ord()
	MOVZX EAX, R11B
	mov [RBP-88], EAX							;assign return value of function to _T6
	mov eax,  [RBP-88]							;_T7 := _T6 = 0
	mov r11d, 0
	cmp eax, r11d
	JE _PASCAL_PRINTSTRINGTYPE_L2
	mov al, 0
	jmp _PASCAL_PRINTSTRINGTYPE_L3
_PASCAL_PRINTSTRINGTYPE_L2:
	mov al, 1
_PASCAL_PRINTSTRINGTYPE_L3:
	mov [RBP-96], al
	mov al, [RBP-96]
	test al,al
	jz _PASCAL_PRINTSTRINGTYPE_TAC_L4_
; write ( ' ' )
	mov AL, 32									;Move literal ' ' into _T8
	mov [RBP-104], AL
	mov RDI,  [RBP-104]
	mov rsi, [RBP-16]
	call fputc wrt ..plt
	jmp _PASCAL_PRINTSTRINGTYPE_TAC_L3_
; ELSE
_PASCAL_PRINTSTRINGTYPE_TAC_L4_:
; write ( s [ i ] )
	mov RAX, [RBP-24]							;Move address of s into _T9
	mov [RBP-112], RAX
	mov eax,  [RBP-8]							;_T10 := i - 1
	mov r11d, 1
	sub eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-120], eax
	mov eax,  [RBP-120]							;_T11 := _T10 * 1
	mov r11d, 1
	imul eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-128], eax
	mov rax,  [RBP-112]							;_T12 := _T9 + _T11 with bounds check removed
	mov r11d,  [RBP-128]
	add rax, r11
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-136], rax
	mov r10, [RBP-136]							;Mov deref of _T12 to _T13
	mov AL, [r10]
	mov [RBP-144], AL
	mov RDI,  [RBP-144]
	mov rsi, [RBP-16]
	call fputc wrt ..plt
_PASCAL_PRINTSTRINGTYPE_TAC_L3_:
; i := i + 1
	mov eax,  [RBP-8]							;_T14 := i + 1
	mov r11d, 1
	add eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-152], eax
	mov EAX,  [RBP-152]							;Move _T14 into i
	mov [RBP-8], EAX
	jmp _PASCAL_PRINTSTRINGTYPE_TAC_L1_
_PASCAL_PRINTSTRINGTYPE_TAC_L2_:
	MOV RSP, RBP								;restore stack pointer
	POP RBP
	RET
