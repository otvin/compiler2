;----------
;
;   compiler2_stringcompare.asm
;	copyright 2025 M. "Fred" Fredericks
;	All Rights Reserved
;	io functions for compiler2
;
;----------

extern _PASCAL_OVERFLOW_ERROR

section .note.GNU-stack noalloc noexec nowrite progbits
section .text
    global _PASCAL_STRING_COMPARE



_PASCAL_STRING_COMPARE:							;Function stringcompare(s:array, t:array, k:integer)

;----------
;
;   _PASCAL_STRING_COMPARE
;       - compares two strings lexicographically.  Each string has to be either a string-type (packed array of chars)
;         or a string literal.
;----------
;   RDI: Address of first string
;   RSI: Address of second string
;   EDX: Length of the strings (first and second string must have same length or the function may crash)
;----------
; Returns: AL (zero-extended into EAX) will have values of:
;   -1 if first string is lexicographically less than the second string
;   0 if the two strings are equal
;   1 if the first string is lexicographically greater than the second string
;----------


	PUSH RBP
	MOV RBP, RSP								;save stack pointer
	SUB RSP, 256								;allocate local storage
												; Parameter s - [RBP-32]
												; Parameter t - [RBP-40]
												; Parameter k - [RBP-48]
												; Function Result - [RBP-8]
												; Local Variable i - [RBP-16]
												; Local Variable ret - [RBP-24]
												; Local Variable _t0 - [RBP-56]
												; Local Variable _t1 - [RBP-64]
												; Local Variable _t2 - [RBP-72]
												; Local Variable _t3 - [RBP-80]
												; Local Variable _t4 - [RBP-88]
												; Local Variable _t5 - [RBP-96]
												; Local Variable _t6 - [RBP-104]
												; Local Variable _t7 - [RBP-112]
												; Local Variable _t8 - [RBP-120]
												; Local Variable _t9 - [RBP-128]
												; Local Variable _t10 - [RBP-136]
												; Local Variable _t11 - [RBP-144]
												; Local Variable _t12 - [RBP-152]
												; Local Variable _t13 - [RBP-160]
												; Local Variable _t14 - [RBP-168]
												; Local Variable _t15 - [RBP-176]
												; Local Variable _t16 - [RBP-184]
												; Local Variable _t17 - [RBP-192]
												; Local Variable _t18 - [RBP-200]
												; Local Variable _t19 - [RBP-208]
												; Local Variable _t20 - [RBP-216]
												; Local Variable _t21 - [RBP-224]
												; Local Variable _t22 - [RBP-232]
												; Local Variable _t23 - [RBP-240]
												; Local Variable _t24 - [RBP-248]
												; Local Variable _t25 - [RBP-256]
	mov [RBP-32], RDI
	mov [RBP-40], RSI
	mov [RBP-48], EDX							;Copy parameter k to stack
; i := 1
	mov EAX, 1									;Move literal '1' into i
	mov [RBP-16], EAX
; ret := 0
	mov EAX, 0									;Move literal '0' into ret
	mov [RBP-24], EAX
; while ( i <= k ) and ( ret = 0 ) do
_PASCAL_STRINGCOMPARE_TAC_L1_:
	mov eax,  [RBP-16]							;_T0 := i <= k
	mov r11d,  [RBP-48]
	cmp eax, r11d
	JLE _PASCAL_STRINGCOMPARE_L0
	mov al, 0
	jmp _PASCAL_STRINGCOMPARE_L1
_PASCAL_STRINGCOMPARE_L0:
	mov al, 1
_PASCAL_STRINGCOMPARE_L1:
	mov [RBP-56], al
	mov eax,  [RBP-24]							;_T1 := ret = 0
	mov r11d, 0
	cmp eax, r11d
	JE _PASCAL_STRINGCOMPARE_L2
	mov al, 0
	jmp _PASCAL_STRINGCOMPARE_L3
_PASCAL_STRINGCOMPARE_L2:
	mov al, 1
_PASCAL_STRINGCOMPARE_L3:
	mov [RBP-64], al
	mov al,  [RBP-56]							;_T2 := _T0 and _T1
	mov r11b,  [RBP-64]
	and al, r11b
	mov [RBP-72], AL
	mov al, [RBP-72]
	test al,al
	jz _PASCAL_STRINGCOMPARE_TAC_L2_
; if s [ i ] < t [ i ] then
	mov RAX, [RBP-32]							;Move address of s into _T3
	mov [RBP-80], RAX
	mov eax,  [RBP-16]							;_T4 := i - 1
	mov r11d, 1
	sub eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-88], eax
	mov eax,  [RBP-88]							;_T5 := _T4 * 1
	mov r11d, 1
	imul eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-96], eax
	mov rax,  [RBP-80]							;_T6 := _T3 + _T5 with bounds check removed
	mov r11d,  [RBP-96]
	add rax, r11
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-104], rax
	mov r10, [RBP-104]							;Mov deref of _T6 to _T7
	mov AL, [r10]
	mov [RBP-112], AL
	mov RAX, [RBP-40]							;Move address of t into _T8
	mov [RBP-120], RAX
	mov eax,  [RBP-16]							;_T9 := i - 1
	mov r11d, 1
	sub eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-128], eax
	mov eax,  [RBP-128]							;_T10 := _T9 * 1
	mov r11d, 1
	imul eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-136], eax
	mov rax,  [RBP-120]							;_T11 := _T8 + _T10 with bounds check removed
	mov r11d,  [RBP-136]
	add rax, r11
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-144], rax
	mov r10, [RBP-144]							;Mov deref of _T11 to _T12
	mov AL, [r10]
	mov [RBP-152], AL
	mov al,  [RBP-112]							;_T13 := _T7 < _T12
	mov r11b,  [RBP-152]
	cmp al, r11b
	JB _PASCAL_STRINGCOMPARE_L4
	mov al, 0
	jmp _PASCAL_STRINGCOMPARE_L5
_PASCAL_STRINGCOMPARE_L4:
	mov al, 1
_PASCAL_STRINGCOMPARE_L5:
	mov [RBP-160], al
	mov al, [RBP-160]
	test al,al
	jz _PASCAL_STRINGCOMPARE_TAC_L4_
; ret := - 1
	mov EAX, -1									;Move literal '-1' into ret
	mov [RBP-24], EAX
	jmp _PASCAL_STRINGCOMPARE_TAC_L3_
; ELSE
_PASCAL_STRINGCOMPARE_TAC_L4_:
; if s [ i ] > t [ i ] then
	mov RAX, [RBP-32]							;Move address of s into _T14
	mov [RBP-168], RAX
	mov eax,  [RBP-16]							;_T15 := i - 1
	mov r11d, 1
	sub eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-176], eax
	mov eax,  [RBP-176]							;_T16 := _T15 * 1
	mov r11d, 1
	imul eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-184], eax
	mov rax,  [RBP-168]							;_T17 := _T14 + _T16 with bounds check removed
	mov r11d,  [RBP-184]
	add rax, r11
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-192], rax
	mov r10, [RBP-192]							;Mov deref of _T17 to _T18
	mov AL, [r10]
	mov [RBP-200], AL
	mov RAX, [RBP-40]							;Move address of t into _T19
	mov [RBP-208], RAX
	mov eax,  [RBP-16]							;_T20 := i - 1
	mov r11d, 1
	sub eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-216], eax
	mov eax,  [RBP-216]							;_T21 := _T20 * 1
	mov r11d, 1
	imul eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-224], eax
	mov rax,  [RBP-208]							;_T22 := _T19 + _T21 with bounds check removed
	mov r11d,  [RBP-224]
	add rax, r11
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-232], rax
	mov r10, [RBP-232]							;Mov deref of _T22 to _T23
	mov AL, [r10]
	mov [RBP-240], AL
	mov al,  [RBP-200]							;_T24 := _T18 > _T23
	mov r11b,  [RBP-240]
	cmp al, r11b
	JA _PASCAL_STRINGCOMPARE_L6
	mov al, 0
	jmp _PASCAL_STRINGCOMPARE_L7
_PASCAL_STRINGCOMPARE_L6:
	mov al, 1
_PASCAL_STRINGCOMPARE_L7:
	mov [RBP-248], al
	mov al, [RBP-248]
	test al,al
	jz _PASCAL_STRINGCOMPARE_TAC_L5_
; ret := 1
	mov EAX, 1									;Move literal '1' into ret
	mov [RBP-24], EAX
_PASCAL_STRINGCOMPARE_TAC_L5_:
_PASCAL_STRINGCOMPARE_TAC_L3_:
; i := i + 1
	mov eax,  [RBP-16]							;_T25 := i + 1
	mov r11d, 1
	add eax, r11d
	jo _PASCAL_OVERFLOW_ERROR
	mov [RBP-256], eax
	mov EAX,  [RBP-256]							;Move _T25 into i
	mov [RBP-16], EAX
	jmp _PASCAL_STRINGCOMPARE_TAC_L1_
_PASCAL_STRINGCOMPARE_TAC_L2_:
; stringcompare := ret
	mov EAX,  [RBP-24]							;Move ret into stringcompare
	mov [RBP-8], EAX
	mov EAX, [RBP-8]							;set up return value
	MOV RSP, RBP								;restore stack pointer
	POP RBP
	RET
