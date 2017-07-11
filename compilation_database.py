import json
import sys
import os
import atexit
import functools


def BuildDatabase(env, target, source, Databases):
    '''Builds a compilation database by setting no_exec, marking all targets as dirty and
    collecting the resulting command lines into a json database.
    This will *disable* your regular build, so this should only be called conditionally.
    '''
    target = target or env.File('#./compile_commands.json')
    if str(target) in Databases:
        return None
    gathered = []

    # Simulate building everything
    env.Decider(lambda t,b,c: True)
    env.SetOption('no_exec', 1)

    def gather_print(cmd, target, source, env):
        files = [{'command': cmd,
                  'file': str(sfile),
                  'directory': os.getcwd(),
                  'output': str(ofile)} for sfile in source for ofile in target]
        gathered.extend(files)

        # Replicate default behaviour as well
        sys.stdout.write(cmd)
        sys.stdout.write("\n")

    env.Replace(PRINT_CMD_LINE_FUNC=gather_print)
    Databases[str(target)] = gathered
    return None

def dump_all(dbmap):
    for path, ds in dbmap.iteritems():
        f = open(path, 'w')
        json.dump(ds, f, indent=1)
        f.close()
        sys.stdout.write('{} entries written to {}\n'.format(len(ds), path))

def generate(env, **kwargs):
    dbmap = {}
    BuildFunction = functools.partial(BuildDatabase, Databases = dbmap)

    env.Append(BUILDERS = {'CompilationDatabase': BuildFunction})
    env.Tool('textfile')

    atexit.register(dump_all, dbmap)

def exists(env):
    return True
