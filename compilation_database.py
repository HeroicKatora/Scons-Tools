import json
import sys
import os
import atexit
import functools

import SCons.Warnings

def dump_all(Databases):
    for path, ds in Databases.iteritems():
        f = open(path, 'w')
        json.dump(ds, f, indent=1)
        f.close()
        sys.stdout.write('{} entries registered to {}\n'.format(len(ds), path))

def get_databases(env):
    global COMPILATION_DATABASES
    return COMPILATION_DATABASES

def set_databases(env, db):
    global COMPILATION_DATABASES
    COMPILATION_DATABASES = db
    atexit.register(dump_all, COMPILATION_DATABASES)
    return

def CompilationDatabase(env, target, source, execute=False):
    '''Builds a compilation database by setting no_exec, marking all targets as
    dirty and collecting the resulting command lines into a json database. You
    probably want to call this at most once in any environment.
    If the build should still execute normally, triggering a complete rebuild,
    `execute` can be set to some True value.
    Multiple calls to different database locations within the same module will
    lead to come of them begin empty. The compilation commands are collected as
    they are executed, which happens after running SConstruct files. As such, only
    the last call within an environment will effectively collect build actions.
    '''
    Databases = get_databases(env)
    target = target or env.File('#./compile_commands.json')
    target = env.File(target)
    target_key = target.abspath
    if target_key not in Databases:
        Databases[target_key] = []
    gathered = Databases[target_key]

    # Simulate building everything
    env.Decider(lambda t,b,c: True)
    if not execute:
        env.SetOption('no_exec', 1)
    elif not env.GetOption('no_exec'):
        class WarnAboutFullCompile(SCons.Warnings.WarningOnByDefault):
            pass
        SCons.Warnings.warn(WarnAboutFullCompile, 'Recompiling ALL targets for database while NOT doing a dry run. This will take a while')

    def gather_print(cmd, target, source, env):
        files = [{'command': cmd,
                  'file': str(sfile),
                  'directory': os.getcwd(),
                  'output': str(ofile)} for sfile in source for ofile in target]
        gathered.extend(files)

        # Replicate default behaviour as well
        sys.stdout.write(cmd)
        sys.stdout.write('\n')

    env.Replace(PRINT_CMD_LINE_FUNC=gather_print)
    return None

def generate(env):
    try:
        Databases = get_databases(env)
    except Exception as ex:
        set_databases(env, {})

    env.Append(BUILDERS = {'CompilationDatabase': CompilationDatabase})

def exists(env):
    return True
