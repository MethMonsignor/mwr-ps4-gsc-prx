[Repository](../README.md) · [Complete reference](reference.md#appendix-a-complete-active-console-builtin-mapping)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

## Appendix A. Complete active console builtin mapping

These are the **69 IDs permitted by profile `0xE6693E47`**, not the entire engine's API. `Function` means VM function dispatch; `Method` means VM entity-method dispatch. The native callback does not receive ordinary C arguments corresponding to the displayed GSC name; see Section 7.

| GSC binding | Console ID | Kind | Native RVA | Registration RVA | Flags |
| --- | --- | --- | --- | --- | --- |
| `isdefined` | `0x0012` | Function | `0x006A6450` | `0x00C60860` | 0 |
| `setdvar` | `0x0017` | Function | `0x006A7200` | `0x00C608D0` | 0 |
| `getdvar` | `0x001C` | Function | `0x006A7940` | `0x00C60920` | 0 |
| `getdvarint` | `0x001D` | Function | `0x006A7B30` | `0x00C60930` | 0 |
| `getdvarfloat` | `0x001E` | Function | `0x006A7DC0` | `0x00C60940` | 0 |
| `getentbynum` | `0x0023` | Function | `0x006A8500` | `0x00C60990` | 1 |
| `spawn` | `0x0030` | Function | `0x006A9920` | `0x00C60A60` | 0 |
| `setslowmotion` | `0x003D` | Function | `0x006AB620` | `0x00C60B60` | 0 |
| `int` | `0x0048` | Function | `0x006AC410` | `0x00C60C20` | 0 |
| `anglestoforward` | `0x006A` | Function | `0x006AF6C0` | `0x00C60EA0` | 0 |
| `getsubstr` | `0x0072` | Function | `0x006B1740` | `0x00C60F80` | 0 |
| `precacheitem` | `0x007A` | Function | `0x006B2C10` | `0x00C61010` | 0 |
| `precacheshader` | `0x007B` | Function | `0x006B2CB0` | `0x00C61020` | 0 |
| `tablelookup` | `0x00C6` | Function | `0x006BF120` | `0x00C616A0` | 0 |
| `tablelookupbyrow` | `0x00C7` | Function | `0x006BF3C0` | `0x00C616C0` | 0 |
| `getentarray` | `0x00EE` | Function | `0x006F5E60` | `0x00C4DEC0` | 0 |
| `newclienthudelem` | `0x00FC` | Function | `0x006651A0` | `0x00C4DFE0` | 0 |
| `map_restart` | `0x0113` | Function | `0x00357FA0` | `0x00C4E1A0` | 0 |
| `exitlevel` | `0x0114` | Function | `0x00358060` | `0x00C4E1B0` | 0 |
| `isbot` | `0x01FC` | Function | `0x00838070` | `0x00C4E770` | 0 |
| `getrankforxp` | `0x02EA` | Function | `0x00361F60` | `0x00C4E9F0` | 0 |
| `attach` | `0x8000` | Method | `0x006CD6F0` | `0x00C61EF0` | 0 |
| `detachall` | `0x8002` | Method | `0x006CDF50` | `0x00C61F20` | 0 |
| `getattachsize` | `0x8003` | Method | `0x006CE8A0` | `0x00C61F40` | 0 |
| `getattachmodelname` | `0x8004` | Method | `0x006CEB10` | `0x00C61F50` | 0 |
| `getattachtagname` | `0x8005` | Method | `0x006CECA0` | `0x00C61F60` | 0 |
| `getattachignorecollision` | `0x8006` | Method | `0x006CEEF0` | `0x00C61F70` | 0 |
| `unlink` | `0x800E` | Method | `0x006D0150` | `0x00C62000` | 0 |
| `islinked` | `0x800F` | Method | `0x006D0210` | `0x00C62010` | 0 |
| `playerlinkto` | `0x8011` | Method | `0x006D0B10` | `0x00C62080` | 0 |
| `delete` | `0x8028` | Method | `0x006D38A0` | `0x00C621E0` | 0 |
| `setmodel` | `0x8029` | Method | `0x006D3A50` | `0x00C62200` | 0 |
| `setmovespeedscale` | `0x808C` | Method | `0x006DBF20` | `0x00C629C0` | 0 |
| `getlocalplayerprofiledata` | `0x809D` | Method | `0x006DD610` | `0x00C62B70` | 0 |
| `setlocalplayerprofiledata` | `0x809E` | Method | `0x006DDAF0` | `0x00C62B80` | 0 |
| `isitemunlocked` | `0x80B0` | Method | `0x006E1440` | `0x00C62CA0` | 0 |
| `getplayerdata` | `0x80B1` | Method | `0x006E1D60` | `0x00C62CB0` | 0 |
| `setplayerdata` | `0x80B2` | Method | `0x006E21E0` | `0x00C62CC0` | 0 |
| `setrank` | `0x80D3` | Method | `0x00658180` | `0x00C5F500` | 0 |
| `fragbuttonpressed` | `0x80E7` | Method | `0x0063EED0` | `0x00C5DF30` | 0 |
| `secondaryoffhandbuttonpressed` | `0x80E8` | Method | `0x0063F0D0` | `0x00C5DF40` | 0 |
| `setvelocity` | `0x80EA` | Method | `0x0063F550` | `0x00C5DF60` | 0 |
| `giveweapon` | `0x80EE` | Method | `0x0063FAA0` | `0x00C5DFF0` | 0 |
| `takeweapon` | `0x80EF` | Method | `0x0063FF90` | `0x00C5E000` | 0 |
| `getcurrentweapon` | `0x80F1` | Method | `0x00640380` | `0x00C5E020` | 0 |
| `hasweapon` | `0x80F4` | Method | `0x006406D0` | `0x00C5E050` | 0 |
| `switchtoweapon` | `0x80F5` | Method | `0x00640A80` | `0x00C5E060` | 0 |
| `givemaxammo` | `0x80F9` | Method | `0x006425B0` | `0x00C5E0F0` | 0 |
| `setorigin` | `0x8100` | Method | `0x006443E0` | `0x00C5E1A0` | 0 |
| `getvelocity` | `0x8101` | Method | `0x00644880` | `0x00C5E1B0` | 0 |
| `getplayerangles` | `0x8103` | Method | `0x00644A30` | `0x00C5E1D0` | 0 |
| `usebuttonpressed` | `0x8104` | Method | `0x00644D10` | `0x00C5E200` | 0 |
| `attackbuttonpressed` | `0x8105` | Method | `0x00644F10` | `0x00C5E210` | 0 |
| `adsbuttonpressed` | `0x8106` | Method | `0x00645110` | `0x00C5E220` | 0 |
| `meleebuttonpressed` | `0x8107` | Method | `0x00645310` | `0x00C5E230` | 0 |
| `disableweapons` | `0x8112` | Method | `0x006467D0` | `0x00C5E300` | 0 |
| `enableweapons` | `0x8113` | Method | `0x00646820` | `0x00C5E310` | 0 |
| `disableoffhandweapons` | `0x8114` | Method | `0x00646870` | `0x00C5E320` | 0 |
| `enableoffhandweapons` | `0x8115` | Method | `0x006468C0` | `0x00C5E330` | 0 |
| `freezecontrols` | `0x811E` | Method | `0x006476C0` | `0x00C5E3F0` | 0 |
| `setclientomnvar` | `0x812D` | Method | `0x00649C30` | `0x00C5E500` | 0 |
| `setperk` | `0x815C` | Method | `0x00650150` | `0x00C5F0F0` | 0 |
| `hasperk` | `0x815D` | Method | `0x00650590` | `0x00C5F100` | 0 |
| `unsetperk` | `0x815F` | Method | `0x00650B70` | `0x00C5F120` | 0 |
| `settext` | `0x82A4` | Method | `0x00666D10` | `0x00C5FDB0` | 0 |
| `setshader` | `0x82A6` | Method | `0x00666E60` | `0x00C5FDD0` | 0 |
| `destroy` | `0x82BA` | Method | `0x00668000` | `0x00C5FF50` | 0 |
| `getlinkedparent` | `0x83E6` | Method | `0x006D0330` | `0x00C62020` | 0 |
| `setcostumemodels` | `0x84B2` | Method | `0x006E5760` | `0x00C62FA0` | 0 |
