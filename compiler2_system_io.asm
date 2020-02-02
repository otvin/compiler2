;----------
;
;   compiler2_system_io.asm
;	copyright 2020 M. "Fred" Fredericks
;	All Rights Reserved
;	io functions for compiler2
;
;----------

extern putchar
extern _PASCAL_OVERFLOW_ERROR

global _PASCAL_PRINTSTRINGTYPE



_PASCAL_PRINTSTRINGTYPE:						;Procedure printstringtype(s:array, k:integer)

;----------
;
;   _PASCAL_PRINTSTRINGTYPE
;       - writes the contents of a string-type (packed array of chars) to screen
;----------
;   RDI: Address of the string-type array to be printed
;   RSI: Length of the string-type array
;----------
; Returns: None
;----------

	PUSH RBP
	MOV RBP, RSP								;save stack pointer
	SUB RSP, 144								;allocate local storage
												; Parameter s - [RBP-16]
												; Parameter k - [RBP-24]
												; Local Variable i - [RBP-8]
												; Local Variable _t0 - [RBP-32]
												; Local Variable _t1 - [RBP-40]
												; Local Variable _t2 - [RBP-48]
												; Local Variable _t3 - [RBP-56]
												; Local Variable _t4 - [RBP-64]
												; Local Variable _t5 - [RBP-72]
												; Local Variable _t6 - [RBP-80]
												; Local Variable _t7 - [RBP-88]
												; Local Variable _t8 - [RBP-96]
												; Local Variable _t9 - [RBP-104]
												; Local Variable _t10 - [RBP-112]
												; Local Variable _t11 - [RBP-120]
												; Local Variable _t12 - [RBP-128]
												; Local Variable _t13 - [RBP-136]
												; Local Variable _t14 - [RBP-144]
	mov [RBP-16], RDI
	mov [RBP-24], ESI							;Copy parameter k to stack
; i := 1 
	mov EAX, 1									;Move literal '1' into i
	mov [RBP-8], EAX
; while i <= k do 
_PASCAL_PRINTSTRINGTYPE_TAC_L1_:
	mov eax,  [RBP-8]							;_T0 := i <= k
	mov r11d,  [RBP-24]
	cmp eax, r11d
	JLE _PASCAL_PRINTSTRINGTYPE_L0
	mov al, 0
	jmp _PASCAL_PRINTSTRINGTYPE_L1
_PASCAL_PRINTSTRINGTYPE_L0:
	mov al, 1
_PASCAL_PRINTSTRINGTYPE_L1:
	mov [RBP-32], al
	mov al, [RBP-32]
	test al,al
	jz _PASCAL_PRINTSTRINGTYPE_TAC_L2_
; if ord ( s [ i ] ) = 0 then 
	mov RAX, [RBP-16]							;Move address of s into _T1
	mov [RBP-40], RAX
	mov eax,  [RBP-8]							;_T2 := i - 1
	mov r11d, 1
	sub eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-48], eax
	mov eax,  [RBP-48]							;_T3 := _T2 * 1
	mov r11d, 1
	imul eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-56], eax
	mov rax,  [RBP-40]							;_T4 := _T1 + _T3 with bounds check removed
	mov r11d,  [RBP-56]
	add rax, r11
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-64], rax
	mov r10, [RBP-64]							;Mov deref of _T4 to _T5
	mov AL, [r10]
	mov [RBP-72], AL
	mov R11B,  [RBP-72]							;parameter _T5 for ord()
	MOVZX EAX, R11B
	mov [RBP-80], EAX							;assign return value of function to _T6
	mov eax,  [RBP-80]							;_T7 := _T6 = 0
	mov r11d, 0
	cmp eax, r11d
	JE _PASCAL_PRINTSTRINGTYPE_L2
	mov al, 0
	jmp _PASCAL_PRINTSTRINGTYPE_L3
_PASCAL_PRINTSTRINGTYPE_L2:
	mov al, 1
_PASCAL_PRINTSTRINGTYPE_L3:
	mov [RBP-88], al
	mov al, [RBP-88]
	test al,al
	jz _PASCAL_PRINTSTRINGTYPE_TAC_L4_
; write ( ' ' ) 
	mov AL, 32									;Move literal ' ' into _T8
	mov [RBP-96], AL
	mov RDI,  [RBP-96]
	call putchar wrt ..plt
	jmp _PASCAL_PRINTSTRINGTYPE_TAC_L3_
; ELSE
_PASCAL_PRINTSTRINGTYPE_TAC_L4_:
; write ( s [ i ] ) 
	mov RAX, [RBP-16]							;Move address of s into _T9
	mov [RBP-104], RAX
	mov eax,  [RBP-8]							;_T10 := i - 1
	mov r11d, 1
	sub eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-112], eax
	mov eax,  [RBP-112]							;_T11 := _T10 * 1
	mov r11d, 1
	imul eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-120], eax
	mov rax,  [RBP-104]							;_T12 := _T9 + _T11 with bounds check removed
	mov r11d,  [RBP-120]
	add rax, r11
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-128], rax
	mov r10, [RBP-128]							;Mov deref of _T12 to _T13
	mov AL, [r10]
	mov [RBP-136], AL
	mov RDI,  [RBP-136]
	call putchar wrt ..plt
_PASCAL_PRINTSTRINGTYPE_TAC_L3_:
; i := i + 1 
	mov eax,  [RBP-8]							;_T14 := i + 1
	mov r11d, 1
	add eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-144], eax
	mov EAX,  [RBP-144]							;Move _T14 into i
	mov [RBP-8], EAX
	jmp _PASCAL_PRINTSTRINGTYPE_TAC_L1_
_PASCAL_PRINTSTRINGTYPE_TAC_L2_:
	MOV RSP, RBP								;restore stack pointer
	POP RBP
	RET
