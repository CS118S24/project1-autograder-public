from multiprocessing import Process, Pipe
import json
import os
import sys
import time

from server_launcher import ServerLauncher, LauncherCmd
import tests


PORT = 8080


def launch_server(pipe):
    launcher = ServerLauncher(pipe)
    launcher.start_server()


def terminate_launcher(pipe):
    pipe.send(LauncherCmd.KILL)


def main():
    result = []
    make = tests.CompileTest()
    make.run()
    result.extend(make.get_result())

    p_local, p_remote = Pipe()
    l = Process(target = launch_server, args=(p_remote,))
    l.start()

    test_list = [
        tests.RequestTest('Basic (TXT)', '/testtxt.txt', 'testtxt.txt', 1)
    ]

    exit_cnt = 0

    for test in test_list:
        print(f'Test {test.name}')
        p_local.send(LauncherCmd.STATUS_CHECK)
        time.sleep(0.2)
        pre_status = p_local.recv()
        test.run('localhost', PORT)
        p_local.send(LauncherCmd.STATUS_CHECK)
        post_status = p_local.recv()
        result.extend(test.get_result())

        if pre_status.value == None and post_status.value != None:
            exit_cnt = exit_cnt + 1

    terminate_launcher(p_local)

    if make.success:
        runtime_summary = {
            'name': 'Runtime Behavior',
            'status': 'passed' if exit_cnt == 0 else 'failed',
            'output': 'Success' if exit_cnt == 0 else f'{exit_cnt} unexpected exits',
            'visibility': 'visible',
        }
    else:
        runtime_summary = {
            'name': 'Runtime Behavior',
            'status': 'failed',
            'output': 'The program does not compile',
            'visibility': 'visible',
        }

    result.append(runtime_summary)

    pts = sum(x.get('score', 0) for x in result)
    # pts = functools.reduce(lambda a, x: a + x.get('score', 0), result, 0)
    print(f'{pts}/1')

    summary_workaround = {
        'name': f'Total points: {pts}/1',
        'status': 'passed',
        'visibility': 'visible',
    }
    result.append(summary_workaround)

    data = { 'tests': result, 'score': pts, 'visibility': 'visible', }
    print(json.dump(data, sys.stdout, indent=4))

    l.join(5)
    if (l.exitcode is None):
        l.kill()

if __name__ == '__main__':
    main()