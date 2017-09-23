import json
import sys
import os
import os.path
import atexit

import SCons.Warnings

def dump_all(Databases):
    uniquifier = lambda db: {(entry['file'], entry['output']): entry for entry in db}
    dbifier = lambda unique: [entry for k, entry in unique.items()]
    for path, ds in Databases.iteritems():
        if os.path.exists(path):
            with open(path, 'r') as existing:
                predb = json.load(existing)
        else:
            predb = []
        predbdict = uniquifier(predb)
        predbdict.update(uniquifier(ds))
        result = dbifier(predbdict)
        with open(path, 'w') as outfile:
            json.dump(result, outfile, indent=1)
        sys.stdout.write('{} entries registered to {}\n'.format(len(ds), path))

def get_databases():
    global COMPILATION_DATABASES
    return COMPILATION_DATABASES

def set_databases(db):
    global COMPILATION_DATABASES
    COMPILATION_DATABASES = db
    atexit.register(dump_all, COMPILATION_DATABASES)
    return

def CompilationDatabase(
        env, target, source,
        execute=False, rebuild=True, silent=False):
    '''Builds a compilation database by setting no_exec, marking all targets as
    dirty and collecting the resulting command lines into a json database. You
    probably want to call this at most once in any environment.
    If the build should still execute normally, triggering a complete rebuild,
    `execute` can be set to some True value.
    Multiple calls to different database locations within the same module will
    lead to come of them begin empty. The compilation commands are collected as
    they are executed, which happens after running SConstruct files. As such,
    only the last call within an environment will effectively collect build
    actions.
    Turning on 'execute' without turning off 'rebuild' will issue a warning and
    require USER INTERACTION as it will issue an unconditional, complete
    rebuild. This can be suppressed by also setting the 'silent' option to True
    '''
    Databases = get_databases()
    target = target or env.File('#./compile_commands.json')
    target = env.File(target)
    target_key = target.abspath
    if target_key not in Databases:
        Databases[target_key] = []
    gathered = Databases[target_key]

    # Simulate building everything
    if rebuild:
        env.Decider(lambda t,b,c: True)
    if not execute:
        env.SetOption('no_exec', 1)
    elif not env.GetOption('no_exec') and rebuild and not silent:
        class WarnAboutFullCompile(SCons.Warnings.WarningOnByDefault):
            pass
        SCons.Warnings.warn(WarnAboutFullCompile, 'Recompiling ALL targets for database while NOT doing a dry run. This will take a while')
        while True:
            inp = input('Continue regardless? y/[n]')
            if inp == 'y':
                break
            elif inp == 'n':
                exit(-1)
            else:
                pass


    def gather_print(cmd, target, source, env):
        files = [{'command': cmd,
                  'file': sfile.abspath,
                  'directory': os.getcwd(),
                  'output': ofile.abspath} for sfile in source for ofile in target]
        gathered.extend(files)

        # Replicate default behaviour as well
        sys.stdout.write(cmd)
        sys.stdout.write('\n')

    env.Replace(PRINT_CMD_LINE_FUNC=gather_print)
    return None

def generate(env):
    try:
        get_databases()
    except Exception as ex:
        set_databases({})

    env.Append(BUILDERS={'CompilationDatabase': CompilationDatabase})

def exists(env):
    return True
