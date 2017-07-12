def CatchRun(env, target, source, test_specs=None, sections=None,
        reporter=None, name=None, success=None, abortx=None,
        out=None, nothrow=None, invisibles=None, warn=None,
        durations=None, input_file=None, order=None,
        rng_seed=None, filenames_as_tags=None, parameters=None):
    ''' For usage of each option see [Catch documentation](https://github.com/philsquared/Catch/blob/master/docs/command-line.md).
    In general, None will leave out the option from the command line, every other value will add the argument.
    Where a list is expected, any iterable will do, using str() to convert the elements to strings beforehand.
    Where a number is expected, this conversion is first enforced via int()
    Where an enum from strings is expected, str() will be called. The result will be checked against the valid values issuing a warning when the value is not known
    Where a bool is expected, bool() will be called on the argument
    Where an argument does not expect and value, it is treated as a bool, except that it will not appear at all when evaluated to false
    Additionally, the parameter arguments can be used to give other parameters
    '''
    import SCons.Warnings
    class UnknownCatchArgument(SCons.Warnings.WarningOnByDefault):
        pass
    command_line = [source[0].get_abspath()]
    if test_specs is not None:
        command_line.extend(map(str, test_specs))
    if sections is not None:
        for sec in map(str, sections):
            command_line.extend(('--section', sec))
    if reporter is not None:
        command_line.extend('--reporter',      str(reporter))
    if name is not None:
        command_line.extend('--name',          str(name))
    if success:
        command_line.extend(('--success',      ))
    if abortx is not None:
        command_line.extend(('--abortx',       int(abortx)))
    if out is not None:
        command_line.extend(('--out',          str(out)))
    if nothrow:
        command_line.extend(('--nothrow',      ))
    if invisibles:
        command_line.extend(('--invisibles',   ))
    if warn is not None:
        command_line.extend(('--warn',         str(warn)))
    if durations is not None:
        _durations = str(durations)
        if _durations not in ('yes', 'no'):
            SCons.Warnings.warn(UnknownCatchArgument, 'Argument "{}" to durations is unknown'.format(_durations))
        command_line.extend(('--durations',    _durations))
    if input_file is not None:
        command_line.extend(('--input-file',   str(input_file)))
    if order is not None:
        _order = str(order)
        if _order not in ('decl', 'lex', 'rand'):
            SCons.Warnings.warn(UnknownCatchArgument, 'Argument "{}" to order is unknown'.format(_order))
        command_line.extend(('--order',        _order))
    if rng_seed is not None:
        command_line.extend(('--rng-seed',     str(rng_seed)))
    if filenames_as_tags:
        command_line.extend(('--filenames-as-tags',))

    action = env.Action(' '.join(command_line), exitstatfunc=lambda t:0)
    env.Alias(target, source, action)
    env.Depends(target, source)
    env.AlwaysBuild(target)


def scan_sources_for_main(env, sources):
    return False

def get_default_main(env):
    if not env.get('DEFAULT_CATCHMAIN'):
        new_main = env.CatchMain()
        env.Replace(DEFAULT_CATCHMAIN=new_main)
    return env.get('DEFAULT_CATCHMAIN')

def CatchTest(env, target, source, test_alias=None, add_main=None, compile_args=None, **kwargs):
    """ Compiles a test from the given sources and runs it. It will scan the source
    code files on whether one of them is a main file and add a shared main object
    where necessary. You can explicitely set this behaviour by setting the keyword
    argument `add_main` to something other than None, convertible to bool.
    """
    if test_alias is None: test_alias = 'catch'
    if (add_main is None and not scan_sources_for_main(env, source)) or add_main:
        main = get_default_main(env)
        source.append(main)

    compile_extra_args = {}
    if compile_args is not None: compile_extra_args.update(compile_args)

    program = env.Program(target=target, source=source, **compile_extra_args)
    run = env.CatchRun(test_alias, program, **kwargs)
    return (program, run)

def CatchMain(env, target, source):
    source = source or ['__catchmain.cpp']
    target = env.File(*source)
    maintext = """#define CATCH_CONFIG_MAIN
#include "catch.hpp"
"""
    cpp_name = env.subst("${TARGET.base}.cpp", target=target)
    sourcefile = env.Textfile(cpp_name, maintext)
    return env.StaticObject(sourcefile)


def generate(env, **kwargs):
    env.Append(BUILDERS = {'CatchRun': CatchRun, 'CatchTest': CatchTest, 'CatchMain': CatchMain})
    env.Tool('textfile')

def exists(env):
    conf = Configure(env)
    return conf.CheckCXXHeader('catch.hpp')
