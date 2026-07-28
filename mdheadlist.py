# Version 1.0

def parse_header(s: str):
    if not isinstance(s, str):
        raise ValueError(f"[ERROR] Input is {type(s)} instead of string")
    for i in range(len(s)):
        if s[i] == '#':
            continue
        elif s[i] != ' ':
            raise ValueError(f"Instead of a valid markdown header, input is: \n\"{s}\"")
        else:
            break
    return {"indent": i-1, "string": s[i+1:], "subheaders": [] }

def normalize_indent(h: dict, i: int):
    h["indent"] = i
    for sh in h["subheaders"]:
        normalize_indent(sh, i+1)

def stringify(h: dict, out: list):
    indent = '\t' * h["indent"]
    out.append(indent + f"- [[#{h["string"]}]]")
    for sh in h["subheaders"]:
        stringify(sh, out)

if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) != 2:
        print("Incorrect number of arguments. Only path to target file needed")
        exit()

    with open(sys.argv[1], 'r', encoding="utf-8") as f:
        strings = f.read().split("\n") 
        
    flag = 0; i = 0
    while i < len(strings):
        s = strings[i]
        if len(s) > 2 and s[0:3] == "```": # entering or exiting code block
            flag = (flag + 1) % 2
        if flag:
            strings.pop(i)
        else:
            i += 1
        
    headers = [ 
        parse_header(s) for s in strings
        if len(s) > 0 and s[0] == '#'
    ]
    
    if len(headers) == 0:
        print("No headers detected")
        exit()
    elif len(headers) > 1:
        i = 1
        while i < len(headers):
            h = headers[i]
            indent = h["indent"]
            hp = headers[i-1]
            if indent <= hp["indent"]:
                i += 1
                continue
            while len(hp["subheaders"]) > 0 and hp["indent"] < indent-1:
                if hp["subheaders"][-1]["indent"] < indent:
                    hp = hp["subheaders"][-1]
                else:
                    break
            hp["subheaders"].append(h)
            headers.pop(i)

    out = []
    for h in headers:
        normalize_indent(h, 0)
        stringify(h, out)

    for s in out:
        print(s)
    exit()