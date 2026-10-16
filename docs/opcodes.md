[Repository](../README.md) · [Complete reference](reference.md#appendix-b-accepted-opcode-widths-and-native-dispatch-anchors)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

## Appendix B. Accepted opcode widths and native dispatch anchors

`Width` includes the opcode byte. `Handler RVA` is the dispatch destination read from the supplied ELF using `tableBase + signed32(table[(opcode - 0x1D)])`, with table base `0x00B8CD64`. These destinations are internal interpreter labels, **not independent callable functions**. Names and validation kinds come from the supplied frozen compiler profile; the address read alone does not prove an operation's semantics.

| Validator kind | Meaning |
|---:|---|
| 0 | Fixed-width instruction with no additional kind-specific validation |
| 1 | Field token; may consume serialized dynamic-name metadata |
| 2 | Unlinked string operand and serialized string |
| 3 | Builtin function ID |
| 4 | Builtin method ID |
| 5 | Local call/function-reference target |
| 6 | Forward/conditional relative branch |
| 7 | Backward relative branch |
| 8 | Signed 32-bit relative jump |

| Opcode | Profile name | Width | Kind | Handler RVA |
| --- | --- | --- | --- | --- |
| `0x1D` | `OP_CastFieldObject` | 1 | 0 | `0x007EADE1` |
| `0x1E` | `OP_SetLocalVariableFieldCached` | 2 | 0 | `0x007EA987` |
| `0x1F` | `OP_plus` | 1 | 0 | `0x007EAB6A` |
| `0x20` | `OP_RemoveLocalVariables` | 2 | 0 | `0x007E890F` |
| `0x21` | `OP_EvalSelfFieldVariableRef` | 3 | 1 | `0x007E8DD2` |
| `0x23` | `OP_GetGameRef` | 1 | 0 | `0x007E8DE9` |
| `0x25` | `OP_EvalLevelFieldVariableRef` | 3 | 1 | `0x007E89CE` |
| `0x27` | `OP_greater` | 1 | 0 | `0x007EB33B` |
| `0x2A` | `OP_dec` | 1 | 0 | `0x007EBDA7` |
| `0x2B` | `OP_JumpOnTrue` | 3 | 6 | `0x007EAB45` |
| `0x2D` | `OP_equality` | 1 | 0 | `0x007EA9F4` |
| `0x30` | `OP_GetVector` | 13 | 0 | `0x007E8E88` |
| `0x32` | `OP_PreScriptCall` | 1 | 0 | `0x007E8559` |
| `0x33` | `OP_GetByte` | 2 | 0 | `0x007E85A4` |
| `0x35` | `OP_SetSelfFieldVariableField` | 3 | 1 | `0x007EB3BF` |
| `0x36` | `OP_JumpOnFalseExpr` | 3 | 6 | `0x007E8373` |
| `0x37` | `OP_GetUndefined` | 1 | 0 | `0x007E8F48` |
| `0x38` | `OP_jumpback` | 3 | 7 | `0x007E829E` |
| `0x39` | `OP_JumpOnTrueExpr` | 3 | 6 | `0x007E8684` |
| `0x3A` | `OP_CallBuiltin0` | 3 | 3 | `0x007E8107` |
| `0x3B` | `OP_CallBuiltin1` | 3 | 3 | `0x007E8107` |
| `0x3C` | `OP_CallBuiltin2` | 3 | 3 | `0x007E8107` |
| `0x3D` | `OP_CallBuiltin3` | 3 | 3 | `0x007E8107` |
| `0x3E` | `OP_CallBuiltin4` | 3 | 3 | `0x007E8107` |
| `0x41` | `OP_SetLocalVariableFieldCached0` | 1 | 0 | `0x007EAAE9` |
| `0x42` | `OP_ClearFieldVariable` | 3 | 1 | `0x007E8B10` |
| `0x43` | `OP_GetLevel` | 1 | 0 | `0x007E8E3D` |
| `0x44` | `OP_size` | 1 | 0 | `0x007E86BE` |
| `0x47` | `OP_AddArray` | 1 | 0 | `0x007EBDFB` |
| `0x49` | `OP_EvalFieldVariable` | 3 | 1 | `0x007E8474` |
| `0x4C` | `OP_Return` | 1 | 0 | `0x007E839E` |
| `0x4D` | `OP_CreateLocalVariable` | 2 | 0 | `0x007E8893` |
| `0x50` | `OP_ScriptLocalMethodCall` | 4 | 5 | `0x007EA361` |
| `0x53` | `OP_GetSelfObject` | 1 | 0 | `0x007E8C24` |
| `0x55` | `OP_SetLevelFieldVariableField` | 3 | 1 | `0x007EAE4E` |
| `0x56` | `OP_EvalArray` | 1 | 0 | `0x007EAF03` |
| `0x57` | `OP_GetSelf` | 1 | 0 | `0x007E873C` |
| `0x58` | `OP_End` | 1 | 0 | `0x007E8773` |
| `0x59` | `OP_EvalSelfFieldVariable` | 3 | 1 | `0x007E8449` |
| `0x5B` | `OP_EvalLocalVariableCached0` | 1 | 0 | `0x007E80D8` |
| `0x5C` | `OP_EvalLocalVariableCached1` | 1 | 0 | `0x007E8529` |
| `0x5D` | `OP_EvalLocalVariableCached2` | 1 | 0 | `0x007E83FB` |
| `0x5E` | `OP_EvalLocalVariableCached3` | 1 | 0 | `0x007E8863` |
| `0x5F` | `OP_EvalLocalVariableCached4` | 1 | 0 | `0x007E8A22` |
| `0x60` | `OP_EvalLocalVariableCached5` | 1 | 0 | `0x007E89A1` |
| `0x61` | `OP_EvalLocalVariableCached` | 2 | 0 | `0x007E84AA` |
| `0x64` | `OP_EvalLocalVariableObjectCached` | 2 | 0 | `0x007E81C9` |
| `0x65` | `OP_ScriptLocalThreadCall` | 5 | 5 | `0x007EA3F6` |
| `0x66` | `OP_GetInteger` | 5 | 0 | `0x007E94BA` |
| `0x67` | `OP_ScriptMethodCallPointer` | 1 | 0 | `0x007E94E0` |
| `0x68` | `OP_checkclearparams` | 1 | 0 | `0x007E8281` |
| `0x6B` | `OP_minus` | 1 | 0 | `0x007EB162` |
| `0x6C` | `OP_ScriptLocalFunctionCall2` | 4 | 5 | `0x007E85CB` |
| `0x6E` | `OP_GetNegByte` | 2 | 0 | `0x007E8D59` |
| `0x6F` | `OP_SafeCreateVariableFieldCached` | 2 | 0 | `0x007E8327` |
| `0x70` | `OP_greater_equal` | 1 | 0 | `0x007EAD26` |
| `0x71` | `OP_vector` | 1 | 0 | `0x007E923D` |
| `0x74` | `OP_ClearArray` | 1 | 0 | `0x007EBA41` |
| `0x75` | `OP_DecTop` | 1 | 0 | `0x007EAD55` |
| `0x76` | `OP_CastBool` | 1 | 0 | `0x007E842B` |
| `0x77` | `OP_EvalArrayRef` | 1 | 0 | `0x007EB1CF` |
| `0x78` | `OP_SetNewLocalVariableFieldCached0` | 2 | 0 | `0x007EAAB4` |
| `0x79` | `OP_GetZero` | 1 | 0 | `0x007E825B` |
| `0x7A` | `OP_wait` | 1 | 0 | `0x007E9705` |
| `0x7B` | `OP_waittill` | 1 | 0 | `0x007E9BC7` |
| `0x80` | `OP_EvalLocalArrayCached` | 2 | 0 | `0x007EAA09` |
| `0x83` | `OP_GetUnsignedShort` | 3 | 0 | `0x007E8AE4` |
| `0x84` | `OP_clearparams` | 1 | 0 | `0x007E90D3` |
| `0x87` | `OP_EmptyArray` | 1 | 0 | `0x007E8BDE` |
| `0x8A` | `OP_EvalFieldVariableRef` | 3 | 1 | `0x007E89DB` |
| `0x8D` | `OP_GetFloat` | 5 | 0 | `0x007E8577` |
| `0x8E` | `OP_EvalLocalVariableRefCached` | 2 | 0 | `0x007E8B96` |
| `0x8F` | `OP_JumpOnFalse` | 3 | 6 | `0x007EA950` |
| `0x93` | `OP_less` | 1 | 0 | `0x007EAA88` |
| `0x94` | `OP_BoolNot` | 1 | 0 | `0x007E870F` |
| `0x97` | `OP_GetString` | 5 | 2 | `0x007E8187` |
| `0x98` | `OP_EvalLevelFieldVariable` | 3 | 1 | `0x007E9A15` |
| `0x99` | `OP_GetLevelObject` | 1 | 0 | `0x007E948A` |
| `0x9A` | `OP_inc` | 1 | 0 | `0x007EAD6C` |
| `0x9B` | `OP_CallBuiltinMethod0` | 3 | 4 | `0x007E87D4` |
| `0x9C` | `OP_CallBuiltinMethod1` | 3 | 4 | `0x007E87D4` |
| `0x9D` | `OP_CallBuiltinMethod2` | 3 | 4 | `0x007E87D4` |
| `0x9E` | `OP_CallBuiltinMethod3` | 3 | 4 | `0x007E87D4` |
| `0x9F` | `OP_CallBuiltinMethod4` | 3 | 4 | `0x007E87D4` |
| `0xA0` | `OP_CallBuiltinMethod5` | 3 | 4 | `0x007E87D4` |
| `0xA4` | `OP_SetVariableField` | 1 | 0 | `0x007EB413` |
| `0xA6` | `OP_GetLocalFunction` | 4 | 5 | `0x007E8E0E` |
| `0xA8` | `OP_multiply` | 1 | 0 | `0x007EB367` |
| `0xAC` | `OP_EvalLocalVariableRefCached0` | 1 | 0 | `0x007EA120` |
| `0xB1` | `OP_jump` | 5 | 8 | `0x007E8701` |
| `0xB4` | `OP_inequality` | 1 | 0 | `0x007EAD01` |
| `0xB5` | `OP_ScriptLocalFunctionCall` | 4 | 5 | `0x007E85E4` |
