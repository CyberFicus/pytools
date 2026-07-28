# CONFIG START
# Change values, but not variable names
# Path where you want to store uploaded plugins:
pspath = ".obsidian-global"
# CONFIG END

import sys, io, os
from datetime import datetime
from shutil import move, copytree
from time import sleep

trash = os.path.join(pspath, "trash")
pspath = os.path.join(pspath, "plugins")
pdname = "plugins" # obsidian plugin directory name

err = "[ERROR]\t" 
dbg = "[DEBUG]\t"
suc = "[OK]   \t"

uploaded = [] # list of uploaded plugins
total = [] # list of all plugins, both uplloaded and not
upde = [] # list of uploaded plugin dir entries
vaults = [] # list of availible vaults
v_pi = {} # vault padded indexes
p_pi = {} # plugin padded indexes

version = "1.0.1"
greetstr = rf"""
{"\t"}     _______   _______   __      __
{"\t"}    \  ___  / \   __  \ \  \    /  /
{"\t"}    | \   / | |  \__\  )|   \  /   |
{"\t"}    | |   | | |   ____/ |    \/    |
{"\t"}    | |   | | |  |      |  |\  /|  |
{"\t"}    | /___\ | |  |      |  | \/ |  |
{"\t"}    /_______\ /__\      /__\    /__\ 

{"\t"}Welcome to Obsidian Plugin Manager v.{version}
"""

# TODO: 
# - obsidian hotkey management via symlinks
# - command to rename specific plugin in specific vaults (only for non uploaded)
# - command to copy specific plugin into specific vault (from another vault or from uploaded)

helpstr = """\t<..._range>
\t\tNumeric range used to select vaults or plugins
\t\tRanges should be filled as follows:
\t\t3       = "select number 3"
\t\t3,6,8   = "select numbers 3, 6 and 8"
\t\t1,3-5,7 = "select numbers 1, 3, 4, 5 and 7"
\t\t*       = "select all available options"
\t\tand so on...

\t<mode>
\t\tPlugin installation mode used to filter targeted plugins:
\t\t- D is directory
\t\t- J is NTFS jucntion
\t\t- S is symlink
\t\tModes can be combined, e.g. DJ or SD

\tclear
\t\tClear console

\t[exit|quit]
\t\tExit plugin manager

\tfind <available_plugin_range> [<mode>]
\t\tFind vaults, where specified plugins are installed in as <mode>
\t\t<mode> is "DJS" by default

\thelp 
\t\tShow command and keyword reference

\tlist <vaults_range> [<mode>]
\t\tList plugins from specified vaults as well as their installation mode
\t\t<mode> is "DJS" by default

\t[remove|delete] <available_plugin_range> from <vault_range> [<mode>]
\tRemove <uploaded_plugin_range> from uploaded
\t\tRemove selected plugins from selected place(s) to trash directory
\t\tCan be filtered by plugin's installation mode
\t\t<mode> is "DJS" by default

\tscan
\t\tScan current directory, update vault and plugin lists

\tshow [plugins|vaults]
\t\tShow list of plugins and vaults.
\t\tPlugins are shown as two lists: uploaded plugins and all available plugins 
\t\tIf keyword is provided, only respective category is shown

\tuplink <uploaded_plugin_range> in <vault_range> [add|replace]
\t\tUplink specified plugins in specified vaults
\t\tBy default, uplinks both installed and not installed plugins
\t\tOptional keywords:
\t\t- add     - only uplink plugins that are not already installed
\t\t- replace - only uplink plugins that are already installed

\tupload <available_plugin_range> from <vault_range>
\t\tUpload plugin(s) form specified vault
\t\tNOTE: only first value from <vault_range> is usede
\t\tAlready uploaded plugins can not be uploaded and must be deleted
"""

def offerhelp(*args, **kwargs):
    print("\tEnter \"help\" to get command and keyword reference")

def c_clear(*args, **kwargs):
    cmd = "cls" if os.name == "nt" else "clear"
    res = os.system(cmd)
    if res != 0:
        print(f"{err}Failed to run \"{cmd}\". Error code: {res}")
            
def c_exit(*args, **kwargs):
    c_clear()
    exit()

def c_find(*args, **kwargs):
    if len(args) < 1:
        print(f"{err}Invalid syntax: at least one parameter needed")
        offerhelp()
        return
    
    modes = {'D', 'J', 'S'}
    mode = modes
    if len(args) > 1:
        mode = parse_mode(args[1], modes)
        if mode is None:
            return
    
    l = total
    r = parserange(args[0], len(l))
    if r is None:
        return
    l = [l[i] for i in r]
                
    ptvs = {p: [] for p in l }
   
    for v in vaults:
        lpd = (pd for pd in scanvault(v) if pd["n"] in l and pd["m"] in mode)
        for pd in lpd:
            ptvs[pd["n"]].append((pd["m"], v["n"]))
            
    for p in l:
        print()
        print(f"\t{p_pi[p]}. {p}: ", end="")
        tl = ptvs[p]
        if len(tl) == 0:
            print("no vaults found")
        else:
            print("\n")
            for t in tl:
                print(f"\t\t[{t[0]}] {v_pi[t[1]]}. {t[1]}")
        print()

def c_help(*args, **kwargs):
    print(helpstr)

def c_list(*args, **kwargs):
    if len(args) < 1:
        print(f"{err}Invalid syntax: at least one parameter needed")
        offerhelp()
        return
    
    modes = {'D', 'J', 'S'}
    mode = modes
    if len(args) > 1:
        mode = parse_mode(args[1], modes)
        if mode is None:
            return
                    
    l = vaults
    r = parserange(args[0], len(l))
    if r is None:
        return
    l = [l[i] for i in r]

    indent = True
    for v in l:
        listplugins(indent=indent, vault=v, mode=mode)
        indent = False

def c_remove(*args, **kwargs):
    if len(args) < 3:
        print(f"{err} Not enough arguments")
        offerhelp()
        return
    if args[1] != 'from':
        print(f"{err} Unknown keyword \"{args[1]}\"")
        offerhelp()
        return
        
    if args[2] == "uploaded":
        pl = uploaded
    else:
        pl = total

        vl = vaults
        vr = parserange(args[2], len(vl))
        if vr is None:
            return
        vl = [vl[i] for i in vr]
        
        modes = {'D', 'J', 'S'}
        mode = modes
        if len(args) > 3:
            mode = parse_mode(args[3], modes)
            if mode == None:
                return
    
    pr = parserange(args[0], len(pl))
    if pr is None:
        return
    pl = [pl[i] for i in pr]

    
    if args[2] == "uploaded":
        listplugins( 
            message = f"These uploaded plugins will be removed", 
            plugin_name_list = pl,
        )
        
        if confirm() == True:
            vpath = os.path.join(trash, "UPLOADED", time())
            os.makedirs(vpath)
            for ppath in (de.path for de in upde if de.name in pl):
                dpath = os.path.join(vpath, os.path.basename(ppath))
                move(ppath, dpath)
            print(f"{suc}Done, all data removed to {vpath}")
            print()
            execute("scan")
        else:
            print("\tOperation canceled")
        return
    
    delflag = False
    indent = True
    for v in vl:
        i, lpd = listplugins(
            indent=indent,
            message= "These plugins will be removed from",
            vault=v,
            plugin_name_list=pl,
            mode=mode
        )
        indent = False
        if i == 0:
            continue
        
        if confirm() == True:
            ppaths = [pd["de"].path for pd in lpd]
            
            vpath = os.path.join(trash, v["n"], time())
            os.makedirs(vpath)
                
            for ppath in ppaths:
                dpath = os.path.join(vpath, os.path.basename(ppath))
                move(ppath, dpath)
            
            print(f"{suc}Done, all data removed to {vpath}")
            delflag = True
        else:
            print("\tOperation canceled")
            if delflag:
                execute("scan")
            return
        print()
    
    if delflag:
        execute("scan")
   
def c_scan(*args, **kwargs):
    dirs = {t[0]:t[1] for t in os.walk(".")}
    tldirs = dirs.pop(".") # top level dirs
    
    # Validate ps and get uploaded plugin dir entries
    if os.path.join(".", pspath) not in dirs:
        print(f"{err}\"{pspath}\" not found in \"{os.getcwd()}\"")
        exit()
    global upde 
    upde = [de for de in os.scandir(pspath) if de.is_dir() ]
    
    # Get available vaults
    global vaults
    vaults = []
    for d in tldirs:
        o = os.path.join(".", d, ".obsidian") 
        if d[0] == '.' or o not in dirs:
            continue
        pp = os.path.join(o, "plugins")
        if pp not in dirs:
            os.mkdir(pp)
        vaults.append({
            "n": d, "pp": pp, # name and .opsidian\plugins path
            "lpde": [ # local plugins dir entries
                de for de in os.scandir(pp) 
                if de.is_dir()
            ], 
            "lpd": None # local plugins data
        })
    vaults.sort(key=lambda e: e["n"])
    
    # Get uploaded plugins
    global uploaded 
    uploaded = sorted([de.name for de in upde])
    
    # Get available plugins
    local = set()
    for v in vaults:
        for de in v["lpde"]:
            local.add(de.name)
    global total
    # Reorder available plugins
    total = uploaded + sorted(list(local - set(uploaded)))
    
    # Get padded indexes for pretty output
    global v_pi, p_pi
    
    v_pi = {} # vault padded indexes
    vlen = len(str(len(vaults)-1))
    for i in range(len(vaults)):
        v_pi[vaults[i]["n"]] = pad(str(i), vlen, r=False)
    
    p_pi = {} # plugin padded indexes
    plen = len(str(len(total)-1))
    for i in range(len(total)):
        p_pi[total[i]] = pad(str(i), plen, r=False)
    
    print(f"{suc}Scan completed\n")
    
def c_show(*args, **kwargs):
    # Validate keyword
    if len(args) > 0:
        mode = args[0]
    else:
        mode = ''
    if not isinstance(mode, str):
        print(f"{err} {mode} is {type(mode)} instead of string")
        raise ValueError()
    keywords = ("plugins", "vaults", '')
    if not mode in keywords:
        print(f"{err}Unknown keyword: {mode}")
        offerhelp()
        return;
    
    print()
    
    # print plugins
    if mode == keywords[0] or mode == keywords[2]:
        u, uw = nlist(uploaded)
        u.insert(0, "\tUPLOADED PLUGINS:")
        u.insert(1, "\t ")
        uw = max(uw, len(u[0]))
        
        t, tw = nlist(total)
        t.insert(0, "\tALL AVAILABLE PLUGINS:")
        t.insert(1, "\t")
        tw = max(tw, len(t[0]))
        
        # Equalize length and width, then print
        for i in range(max(len(u), len(t))):
            if i == len(u):
                u.append(pad('\t', uw))
            else:
                u[i] = pad(u[i], uw)

            if i == len(t):
                t.append(pad('\t', tw))
            else:
                t[i] = pad(t[i], tw)
            
            print(u[i], t[i])
    
    if mode == keywords[2]:
        print();
    
    if mode == keywords[1] or mode == keywords[2]:
        print("\tAVAILABLE VAULTS:\n")
        vs = [v["n"] for v in vaults]
        for s in nlist(vs)[0]:
            print(s)
        print()

def c_uplink(*args, **kwargs):
    if len(args) < 3:
        print(f"{err} Not enough arguments")
        offerhelp()
        return
    if args[1] != 'in':
        print(f"{err} Unknown keyword \"{args[1]}\"")
        offerhelp()
        return
        
    pl = uploaded
    pr = parserange(args[0], len(pl))
    if pr is None:
        return
    pl = [pl[i] for i in pr]
    
    vl = vaults
    vr = parserange(args[2], len(vl))
    if vr is None:
        return
    vl = [vl[i] for i in vr]
    
    mode_add = True
    mode_replace = True
    if len(args) > 3:
        if args[3] == "add":
            mode_replace = False
        elif args[3] == "replace":
            mode_add = False
        else:
            print(f"{err}Unknown keyword: {args[2]}")
            offerhelp()
            return
    
    change_flag = False
    indent = True
    for v in vl:
        vn=v["n"]
        pde = v["lpde"]
        
        to_add = []
        if mode_add:
            to_add = [
                p for p in pl
                if p not in [
                    de.name for de in pde
                    if de.is_dir()
                ]
            ]
        
        to_replace = []
        if mode_replace:
            to_replace = [
                de for de in pde 
                if 
                    de.name in pl and
                    not de.is_symlink() and
                    not de.is_junction()
            ]
            replace_names = [de.name for de in to_replace]
            to_add = to_add + replace_names
        
        i, _ = listplugins(
            message="These plugins will be uplinked in",
            vault=v,
            plugin_name_list=to_add,
            indent=indent
        )
        if i == 0:
            indent = False
            continue
        else:
            indent = True
        
        if len(to_replace) > 0:
            listplugins(
                message="These plugins will be replaced in",
                vault=v,
                plugin_name_list=replace_names,
                indent=False
            )

        if confirm() == True:
            if mode_replace:
                trash_path = os.path.join(trash, vn, time())
                os.makedirs(trash_path) 
            
                for de in to_replace:
                    dst_path = os.path.join(trash_path, de.name)
                    move(de.path, dst_path)                
                print(f"{suc}Done, all data removed to {trash_path}")
                change_flag = True
        
            for p_name in to_add:
                if os.name == "nt":
                    p_path = os.path.join(pspath, p_name)
                    j_path = os.path.join(v["pp"], p_name)
                    cmd = rf'mklink /J "{j_path}" "{p_path}" > nul'
                    res = os.system(cmd)
                    if res != 0:
                        print(f"{err}Failed to run \"{cmd}\". Error code: {res}")
                        if change_flag:
                            execute("scan")
                        return
                    change_flag = True
                else:
                    raise NotImplementedError()
        else:
            print("\tOperation canceled")
            if change_flag:
                execute("scan")
            return
        
        print(f"{suc}Uplink in {v_pi[vn]}. {vn} done")
        print()
    
    if change_flag:
        execute("scan")

def c_upload(*args, **kwargs):
    if len(args) < 3:
        print(f"{err} Not enough arguments")
        offerhelp()
        return
    if args[1] != 'from':
        print(f"{err} Unknown keyword \"{args[1]}\"")
        offerhelp()
        return
        
    pl = total
    pr = parserange(args[0], len(pl))
    if pr is None:
        return
    pl = [pl[i] for i in pr]
        
    
    vl = vaults
    vr = parserange(args[2], len(vl))
    if vr is None:
        return
    v = vl[min(vr)]
    names = [de.name for de in v["lpde"] if de.name in pl]

    errflag = False
    i = 0
    while i < len(pl):
        p = pl[i]
        if p not in names:
            print(f"{err}{p} is not installed in {v["n"]}")
            errflag = True
            pl.remove(p)
            continue
        if p in uploaded:
            print(f"{err}{p} is alrady uploaded")
            errflag = True
            pl.remove(p)
            continue
        i += 1
    if errflag:
        offerhelp()
    
    i, _ = listplugins(
        message="Following plugins will be uploaded from",
        vault=v,
        plugin_name_list=pl
    )
    if i == 0:
        return
    
    if confirm() == False:
        print("\tUpload canceled")
        return
    
    pde = [de for de in v["lpde"] if de.name in pl]
    for de in pde:
        dpath = os.path.join(pspath, de.name)
        copytree(de.path, dpath, symlinks=True, ignore_dangling_symlinks=True)
    
    print(f"{suc}Upload completed")
    execute("scan")

commands = {
    c.__name__[2:]: c 
    for c in (
        c_clear, 
        c_exit, 
        c_find, 
        c_help, 
        c_list, 
        c_remove, 
        c_scan, 
        c_show,
        c_uplink,
        c_upload
    )
}
commands["quit"] = c_exit
commands["delete"] = c_remove

def execute(command: str, *args, **kwargs):
    command = command.strip()
    if ";" in command:
        for part in command.split(';'):
            execute(part)
        return
    
    if command == '':
        return
    if not isinstance(command, str):
        print(f"{err}Command is {type(command)} instead of string")
        return
    if command in commands:
        commands[command](*args, **kwargs)
    else:
        l = [s for s in command.split(' ') if s != '']
        if l[0] not in commands:
            print(f"{err}Unknown command: \"{l[0]}\"")
            offerhelp()
            return
        commands[l[0]](*l[1:], *args, **kwargs)

def pad(s: str, l: int, *, r:bool=True, c:str=' '):
    if not isinstance(s, str):
        s = str(s)
    if len(s)-1 > l:
        raise ValueError(f"{s} is longer than {l}")
    if r:
        return s + (l - len(s)) * c
    else:
        return (l - len(s)) * c + s

def nlist(l: list):
    llen = len(str(len(l)-1))
    t = []
    for i in range(len(l)):
        n = pad(i,llen,r=False)
        t.append(f"\t{n}. {l[i]}")
    return t, max(len(s) for s in t)

def scanvault(v, *, rescan:bool=False, **kwargs):
    lpd = v["lpd"]
    if lpd is not None and rescan == False:
        return lpd
    if rescan == True:
        v["lpde"] ==  [de for de in os.scandir(v["pp"]) if de.is_dir()]
    
    lpd = []
    v["lpd"] = lpd
    slen = len(str(len(vaults)))-1
    
    for de in v["lpde"]:
        if de.is_junction():
            m = 'J'
        elif de.is_symlink():
            m = 'S'
        elif de.is_dir():
            m = 'D'
        else:
            raise ValueError() # should never happen!
        
        pd = {
            "n": de.name,
            "m": m,
            "i": total.index(de.name),
            "de": de
        }
        lpd.append(pd)
    
    lpd.sort(key=lambda e: e['i'])
    return lpd

rcs = set('1234567890,-*') # range char set
def parserange(rangestr: str, ceiling: int):    
    rs = rangestr.strip()
    if len(set(rs) - rcs) > 0:
        print(f"{err}Invalid syntax in numeric range '{rangestr}': forbidden symbols")
        offerhelp()
        return None
    
    r = set()
    for s in rs.split(','):
        if '*' in s:
            return [i for i in range(0,ceiling)]
        if '-' in s:
            lr = s.split('-')
            if len(lr) != 2 or lr[0] == '' or lr[1] == '':
                print(f"{err}Invalid syntax in range \"{s}\"")
                offerhelp()
                return None
            
            left = int(lr[0])
            right = int(lr[1])
            if left >= right:
                print(f"{err}Invalid syntax in range \"s\": {left} >= {right}")
                offerhelp()
                return None
            if right >= ceiling:
                print(f"{err}{right} is too big: must be below {ceiling}")
                offerhelp()
                return None
            for i in range(left, right+1):
                r.add(i)
            
        else:
            i = int(s)
            if i >= ceiling:
                print(f"{err}Numeric range element {i} is too big: must be below {ceiling}")
                offerhelp()
                return None
            r.add(i)
        
    return sorted(list(r))
    
def parse_mode(mode_arg: str, modes: set):
    if not isinstance(mode_arg, str):
        mode_arg = str(mode_arg)
    if not isinstance(modes, set):
        modes = set(modes)
    
    mode_arg = set(mode_arg)
    diff = mode_arg - modes;
    if len(diff) > 0:
        print(f"{err}Forbidden symbols: {diff}")
        offerhelp()
        return None
    return modes & mode_arg
    
def confirm():
    msg = "\tDo you confirm? (Y/N): "
    while True:
        print(msg, end="")
        i = input().strip().upper()
        if i == 'Y':
            return True
        if i == 'N':
            return False
    
def time():
    s = str(datetime.now())
    return (s[:10] + s[11:]).replace(':', '-')

def listplugins(
    *args, 
    message = None, 
    vault=None, 
    plugin_name_list = None, 
    mode=None,
    indent=True
):
    # Valid input:
    # vault, [plugin_name_list], mode, [messgage]
    #[vault], plugin_name_list, [messgage]

    if indent:
        print()
    if message is None:
        message = ""
    vault_str = ": "
    if vault is not None:
        vn = vault["n"]
        vault_str = f" {v_pi[vn]}. {vn}" + vault_str
    
    print("\t" + message + vault_str, end=" ")
    
    if mode is not None: # need to filter by mode
        if vault is None: 
            raise ValueError() # should never happen!
        lpd = [pd for pd in scanvault(vault) if pd["m"] in mode]
        if plugin_name_list is not None:
            lpd = [pd for pd in lpd if pd["n"] in plugin_name_list]
        if len(lpd) == 0:
            print("none\n")
            return 0, None
        lpd.sort(key=lambda pd: pd["i"])
        
        print("\n")
        i = 0
        for pd in lpd:
            i += 1
            pn = pd["n"]
            print(f"\t\t[{pd["m"]}] {p_pi[pn]}. {pn}")
        print()
        return i, lpd
    elif plugin_name_list is not None:
        if len(plugin_name_list) == 0:
            print("none\n")
            return 0, None
        
        print("\n")
        i = 0
        for pn in plugin_name_list:
            i += 1
            print(f"\t\t{p_pi[pn]}. {pn}")
        print()
        return i, None
    else:
        raise ValueError() # should never happen!

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print(greetstr)
    if len(sys.argv) != 2:
        print(
            f"{err}Incorrect number of arguments. " +
            "Only path to target directory needed"
        )
        exit()
    os.chdir(sys.argv[1])
    
    if os.path.exists(trash):
        if os.path.isfile(trash):
            print(f"{err}Unable to initialize trash directory: {trash} is file")
            exit()
    else:
        os.makedirs(trash)
        print(f"{suc}Trash directory created at \"{trash}\"")
    
    execute("scan")
    execute("show")
    offerhelp()
    
    try:
        while True:
            print(">", end="")
            execute(input())
    except KeyboardInterrupt:
        print("\n^C recieved, exiting...")
        exit
        
if __name__ == '__main__':
    main()