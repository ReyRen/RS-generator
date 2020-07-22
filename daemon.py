#!/usr/bin/env python
#encoding: utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
#usage: 启动: python daemon_class.py start
#       关闭: python daemon_class.py stop
#       状态: python daemon_class.py status
#       重启: python daemon_class.py restart
#       查看: ps -axj | grep daemon_class
 
NAMESPACE="ai"
GPU_NUM=0
CPU_NUM=0
DELETE=0
EXEC_TRUE="true"
DISTRIBUTION="horovod"

import atexit, os, time, signal,json
from tornado import ioloop
from tornado.web import Application
from tornado.websocket import WebSocketHandler
import xml.etree.ElementTree as ET
import subprocess

'''自定义switch/case'''
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop """
        yield self.match
        raise StopIteration
    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False


def execute_RS_generator(tag, text):
    global NAMESPACE
    global GPU_NUM
    global CPU_NUM
    global DELETE
    global EXEC_TRUE
    global DISTRIBUTION

    exec_command = "/bin/bash main.sh "
    
    for case in switch(tag):
        if case('namespace'): 
            NAMESPACE = text
            break
        if case('gpu'):
            GPU_NUM = text
            break
        if case('cpu'):
            CPU_NUM = text
            break
        if case('execuation'):
            EXEC_TRUE = text
            break
        if case('distribution'):
            DISTRIBUTION = text
            break
    exec_command = "/bin/bash main.sh " + " -n " + NAMESPACE + " -g " + bytes(GPU_NUM) + " -c " + bytes(CPU_NUM) + " -e " +  EXEC_TRUE + " -d " + DISTRIBUTION
    
    return exec_command

def get_resources_capacity(rsType):

    for case in switch(rsType):
        if case('gpu'):
            strings_capacity = r"kubectl describe nodes  |  tr -d '\000' | sed -n -e '/^Name/,/Roles/p' -e '/^Capacity/,/Allocatable/p' -e '/^Allocated resources/,/Events/p' | grep -e Name  -e  nvidia.com  | perl -pe 's/\n//'  |  perl -pe 's/Name:/\n/g' | sed 's/nvidia.com\/gpu:\?//g'  | sed '1s/^/Node Available(GPUs)  Used(GPUs)/' | sed 's/$/0 0 0/'  | awk '{print $1, $2, $3}'  | column -t | awk '{sum += $2};END {print sum}'"
            strings_used = r"kubectl describe nodes  |  tr -d '\000' | sed -n -e '/^Name/,/Roles/p' -e '/^Capacity/,/Allocatable/p' -e '/^Allocated resources/,/Events/p' | grep -e Name  -e  nvidia.com  | perl -pe 's/\n//'  |  perl -pe 's/Name:/\n/g' | sed 's/nvidia.com\/gpu:\?//g'  | sed '1s/^/Node Available(GPUs)  Used(GPUs)/' | sed 's/$/0 0 0/'  | awk '{print $1, $2, $3}'  | column -t | awk '{sum += $3};END {print sum}'"
            f = os.popen(strings_capacity)
            num_capacity = f.read()
            f1 = os.popen(strings_used)
            num_used = f1.read()
            f.close()
            f1.close()

    return int(num_capacity), int(num_used), int(num_capacity)-int(num_used)


class EchoWebSocket(WebSocketHandler):
    def open(self):
        fd = open(log_fn, 'w+')
        fd.truncate()
        fd.write("connection opened\n")

        # get rs capacity()
        str_capacity,str_used,str_avaliable = get_resources_capacity("gpu")

        rs_msg = {'gpuCapacity':str_capacity, 'gpuUsed':str_used, 'gpuAvailable':str(str_avaliable)}
        
        self.write_message(json.dumps(rs_msg))

        # record to log file
        fd.write("gpu capacity:" + str(str_capacity) + "\n")
        fd.write("gpu used:" + str(str_used) + "\n")
        fd.write("gpu available:" + str(str_avaliable) + "\n")

        fd.close()

    def on_message(self, message):
        res_exec_cmd = ""
        global proc

        fd = open(log_fn, 'w+')
        decouplefd = open(".env", 'w+')
        decouplefd.truncate()
        #os.system('/bin/bash server.sh %s'%(message))# system.os("xxxx%s %s" % (paramA,paramB)
        xml = ET.fromstring(message)

        flag = 0
        for table in xml.iter('information'):
            for child in table:
                #print child.tag, child.text
                if str(child.tag) == "trainingCommand" and flag == 0:
                    for case in switch(str(child.text)):
                        if case('START'):
                            #start training
                            flag = 1
                            break
                        if case('STOP'):
                            #stop training
                            flag = 2
                            break
                elif str(child.tag) == "selectedModelUrl" and flag == 1:
                    decouplefd.write("MODEL_URL = " + str(child.text) + "\n")
                elif str(child.tag) == "selectedDatasetUrl" and flag == 1:
                    decouplefd.write("DATASET_URL = " + str(child.text) + "\n")
                elif str(child.tag) == "selectedNodes" and flag == 1:
                    res_exec_cmd = execute_RS_generator("gpu",str(child.text))
                elif str(child.tag) == "learningRate" and flag == 1:
                    decouplefd.write("LEARNING_RATE = " + str(child.text) + "\n")
                elif str(child.tag) == "epochNum1" and flag == 1:
                    #NOTE: 第一阶段遍历数据集次数
                    decouplefd.write("EPOCH_NUM1 = " + str(child.text) + "\n")
                elif str(child.tag) == "epochNum2" and flag == 1:
                    #NOTE: 第二阶段遍历数据集次数
                    decouplefd.write("EPOCH_NUM2 = " + str(child.text) + "\n")
                elif str(child.tag) == "batchSize" and flag == 1:
                    #NOTE:batch size
                    decouplefd.write("BATCH_SIZE = " + str(child.text) + "\n")
                elif str(child.tag) == "selectedDataType" and flag == 1:
                    # float32/16
                    decouplefd.write("DATA_TYPE = " + str(child.text) + "\n")
                elif str(child.tag) == "saveNum" and flag == 1:
                    #NOTE: 保存的个数
                    decouplefd.write("SAVE_NUM = " + str(child.text) + "\n")

        self.write_message(u"success")
        fd.flush()
        decouplefd.flush()
        
        if flag == 2:
            fd.write("stop the execuation\n")
            fd.flush()
            os.system("ps aux | grep ./generate | sed -n \"1, 1p\" | awk '{print $2}' | xargs kill -9")
            os.system("kubectl delete pods,services -n ai -l run=radar")
            fd.write("Terminated\n")
            ##subprocess.Popen.kill()
            #os.killpg(proc.pid, signal.SIGTERM)
            os.system("rm -rf .podFile/*")
            fd.write("Terminated\n")
            fd.flush()
        if flag == 1:
            # record to log file
            fd.write(res_exec_cmd + "\n")
            fd.write("start to execute RS-generator\n")
#            res = subprocess.call(res_exec_cmd, bufsize=0, stdout=fd, shell = True)
            res = subprocess.Popen(res_exec_cmd, bufsize=0, stdout=fd, shell = True) # 子父进程并行执行，否则停止命令会接受不到
#            res = os.system(res_exec_cmd)
            fd.write("the execute result = " + bytes(res))


        #self.write_message(u"success")
        decouplefd.close()
        fd.close()

    def on_close(self):
        fd = open(log_fn, 'a')
        fd.write("connection closed\n")
        fd.close()

    def check_origin(self, origin):
        return True
 
class CDaemon:
    '''
    a generic daemon class.
    usage: subclass the CDaemon class and override the run() method
    stderr  表示错误日志文件绝对路径, 收集启动过程中的错误日志
    verbose 表示将启动运行过程中的异常错误信息打印到终端,便于调试,建议非调试模式下关闭, 默认为1, 表示开启
    save_path 表示守护进程pid文件的绝对路径
    '''
    def __init__(self, save_path, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull, home_dir='.', umask=022, verbose=1):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = save_path #pid文件绝对路径
        self.home_dir = home_dir
        self.verbose = verbose #调试开关
        self.umask = umask
        self.daemon_alive = True
 
    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)
 
        os.chdir(self.home_dir)
        os.setsid()
        os.umask(self.umask)
 
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)
 
        sys.stdout.flush()
        sys.stderr.flush()
 
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        if self.stderr:
            se = file(self.stderr, 'a+', 0)
        else:
            se = so
 
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
 
        def sig_handler(signum, frame):
            self.daemon_alive = False
        signal.signal(signal.SIGTERM, sig_handler)
        signal.signal(signal.SIGINT, sig_handler)
 
        if self.verbose >= 1:
            print 'daemon process started ...'
 
        atexit.register(self.del_pid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write('%s\n' % pid)
 
    def get_pid(self):
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None
        return pid
 
    def del_pid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)
 
    def start(self, *args, **kwargs):
        if self.verbose >= 1:
            print 'ready to starting ......'
        #check for a pid file to see if the daemon already runs
        pid = self.get_pid()
        if pid:
            msg = 'pid file %s already exists, is it already running?\n'
            sys.stderr.write(msg % self.pidfile)
            sys.exit(1)
        #start the daemon
        self.daemonize()
        self.run(*args, **kwargs)
 
    def stop(self):
        if self.verbose >= 1:
            print 'stopping ...'
        pid = self.get_pid()
        if not pid:
            msg = 'pid file [%s] does not exist. Not running?\n' % self.pidfile
            sys.stderr.write(msg)
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            return
        #try to kill the daemon process
        try:
            i = 0
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                i = i + 1
                if i % 10 == 0:
                    os.kill(pid, signal.SIGHUP)
        except OSError, err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)
            if self.verbose >= 1:
                print 'Stopped!'
 
    def restart(self, *args, **kwargs):
        self.stop()
        self.start(*args, **kwargs)
 
    def is_running(self):
        pid = self.get_pid()
        #print(pid)
        return pid and os.path.exists('/proc/%d' % pid)
 
    def run(self, *args, **kwargs):
        'NOTE: override the method in subclass'
        print 'base class run()'
 
class ClientDaemon(CDaemon):
    def __init__(self, name, save_path, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull, home_dir='.', umask=022, verbose=1):
        CDaemon.__init__(self, save_path, stdin, stdout, stderr, home_dir, umask, verbose)
        self.name = name #派生守护进程类的名称
 
    def run(self, output_fn, **kwargs):
#        fd = open(output_fn, 'w')
        while True:
            application = Application([
                (r"/", EchoWebSocket),
            ])

            application.listen(9090)
            ioloop.IOLoop.current().start()
#            line = time.ctime() + '\n'
#            fd.write(line)
#            fd.flush()
#            time.sleep(1)
        #fd.close()
 
 
if __name__ == '__main__':
    help_msg = 'Usage: python %s <start|stop|restart|status>' % sys.argv[0]
    if len(sys.argv) != 2:
        print help_msg
        sys.exit(1)
    p_name = 'serverd' #守护进程名称
    pid_fn = '/tmp/daemon_class.pid' #守护进程pid文件的绝对路径
    global log_fn 
    log_fn = '/tmp/daemon_class.log' #守护进程日志文件的绝对路径
    err_fn = '/tmp/daemon_class.err.log' #守护进程启动过程中的错误日志,内部出错能从这里看到
    cD = ClientDaemon(p_name, pid_fn, stderr=err_fn, verbose=1)
 
    if sys.argv[1] == 'start':
        cD.start(log_fn)
    elif sys.argv[1] == 'stop':
        cD.stop()
    elif sys.argv[1] == 'restart':
        cD.restart(log_fn)
    elif sys.argv[1] == 'status':
        alive = cD.is_running()
        if alive:
            print 'process [%s] is running ......' % cD.get_pid()
        else:
            print 'daemon process [%s] stopped' %cD.name
    else:
        print 'invalid argument!'
        print help_msg
