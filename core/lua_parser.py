"""Safe parser for the Lua table-literal subset written by Balatro.
Never executes the Lua source contained in a .jkr file.
"""
from __future__ import annotations
import re

class LuaParseError(ValueError):
    pass

class LuaTableParser:
    def __init__(self, source: str):
        self.s = source
        self.i = 0

    def _ws(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def _eat(self, token: str) -> bool:
        self._ws()
        if self.s.startswith(token, self.i):
            self.i += len(token)
            return True
        return False

    def _string(self) -> str:
        if self.i >= len(self.s) or self.s[self.i] != '"':
            raise LuaParseError(f"Expected string at offset {self.i}")
        self.i += 1
        out = []
        while self.i < len(self.s):
            ch = self.s[self.i]
            self.i += 1
            if ch == '"':
                return "".join(out)
            if ch != "\\":
                out.append(ch)
                continue
            if self.i >= len(self.s):
                break
            esc = self.s[self.i]
            self.i += 1
            simple = {"n":"\n", "r":"\r", "t":"\t", '"':'"', "\\":"\\", "'":"'"}
            if esc in simple:
                out.append(simple[esc])
            elif esc.isdigit():
                digits = esc
                for _ in range(2):
                    if self.i < len(self.s) and self.s[self.i].isdigit():
                        digits += self.s[self.i]
                        self.i += 1
                out.append(chr(int(digits) % 256))
            else:
                out.append(esc)
        raise LuaParseError("Unterminated Lua string")

    def value(self):
        self._ws()
        if self.i >= len(self.s):
            raise LuaParseError("Unexpected end of input")
        if self.s.startswith("return", self.i):
            self.i += 6
            return self.value()
        ch = self.s[self.i]
        if ch == "{":
            return self._table()
        if ch == '"':
            return self._string()
        for word, value in (("true", True), ("false", False), ("nil", None)):
            if self.s.startswith(word, self.i):
                end = self.i + len(word)
                if end == len(self.s) or not (self.s[end].isalnum() or self.s[end] == "_"):
                    self.i = end
                    return value
        number = re.match(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?", self.s[self.i:])
        if number:
            token = number.group(0)
            self.i += len(token)
            result = float(token)
            return int(result) if result.is_integer() else result
        raise LuaParseError(f"Unsupported Lua value at offset {self.i}: {self.s[self.i:self.i+32]!r}")

    def _table(self):
        if not self._eat("{"):
            raise LuaParseError(f"Expected table at offset {self.i}")
        result = {}
        implicit = 1
        while True:
            self._ws()
            if self._eat("}"):
                return result
            if self.i >= len(self.s):
                raise LuaParseError("Unterminated table")
            if self._eat("["):
                key = self.value()
                if not self._eat("]") or not self._eat("="):
                    raise LuaParseError(f"Malformed keyed table entry at offset {self.i}")
                result[key] = self.value()
            else:
                save_i = self.i
                ident = re.match(r"[A-Za-z_][A-Za-z0-9_]*", self.s[self.i:])
                if ident:
                    name = ident.group(0)
                    self.i += len(name)
                    if self._eat("="):
                        result[name] = self.value()
                    else:
                        self.i = save_i
                        result[implicit] = self.value()
                        implicit += 1
                else:
                    result[implicit] = self.value()
                    implicit += 1
            self._eat(",")
            self._eat(";")

def parse_lua_table(source: str):
    parser = LuaTableParser(source)
    value = parser.value()
    parser._ws()
    if parser.i != len(source):
        # Balatro's serializer should produce one return table only.
        tail = source[parser.i:].strip()
        if tail:
            raise LuaParseError(f"Unexpected trailing content at offset {parser.i}")
    if not isinstance(value, dict):
        raise LuaParseError("Save root is not a Lua table")
    return value
