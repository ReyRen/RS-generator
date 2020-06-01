#!/usr/bin/env bash

NAMESPACE="default"
GPU_NUM=0
CPU_NUM=0
MAX_GPU_NUM=3
DELETE=0
EXEC_TRUE=true

#
# usage:
# If you want to use 2 GPUs to do the trainning:
#	./main.sh -g 2
# If you want to specify the NAMESPACE with 3 GPUs to do the trainning:(default namespace will be use if without -n NAMESPACE)
#	./main.sh -n ai -g 3
# If you want to use 2 CPUs to do the trainning:
#	./main.sh -c 2
# If you want to specify the NAMESPACE with 3 CPUs to do the trainning:(default namespace will be use if without -n NAMESPACE)
#	./main.sh -n ai -c 2
# If you want to mix GPUs and CPUs:
#	./main.sh -n ai -g 2 -c 2
# If you only want create those RS files() instead of executing it:(default will execute)
#	./main.sh balabala -e false
# If you want to delete all RS in the NAMESPACE:(default is by default:))
#	./main.sh -D ai
#

function help_me() {
	echo "Usage: ./main.sh -n [namespace] -g [GPUNUM] -c [CPUNUM] -e [true/false] -D [NAMESPACE] -h"
	echo "-h		This message."
	echo "-D [namespace]	Delete all RS in the specific NAMESPACE"
	echo "-n [namespace]	create NAMESPACE when create RS"
	echo "-g [GPUNUM]	trainning with GPUNUM GPUs, 0 is nothing to create"
	echo "-g [CPUNUM]	trainning with GPUNUM CPUs, 0 is nothing to create"
	echo "-e [true/false]	true(default) means it will create RS files and execute or without execution"
}

function get_opts() {
	while getopts "hD:n:g:c:e:" option; do
		case $option in
			e)
				EXEC_TRUE=$OPTARG
				;;
			n)
				NAMESPACE=$OPTARG
				;;
			g)
				GPU_NUM=$OPTARG
				;;
			c)
				CPU_NUM=$OPTARG
				;;
			D)
				# Since the default NAMESPACE is 'default', and delete it by accident is very dangerous. so
				# the paramater is required.
				DELETE=1
				NAMESPACE=$OPTARG
				;;
			h)
				help_me
				exit 1
				;;
			*)
				help_me
				exit 1
				;;
		esac
	done

	# TODO: please modify this value
	if [ $GPU_NUM -gt $MAX_GPU_NUM ]; then
		echo "Only $MAX_GPU_NUM GPUs support"
		exit 2
	fi
}

function generate_rs_file() {
	if [ $GPU_NUM -gt 0 ]; then
		# use GPU
		if [ $CPU_NUM -gt 0 ]; then
			# use GPU and CPU
			./generate_gpu_rs.py $NAMESPACE $GPU_NUM $EXEC_TRUE
			./generate_cpu_rs.py $NAMESPACE $CPU_NUM $EXEC_TRUE
		else
			# only GPU
			./generate_gpu_rs.py $NAMESPACE $GPU_NUM $EXEC_TRUE
		fi
	elif [ $CPU_NUM -gt 0 ]; then
		# use CPU without GPU
		./generate_cpu_rs.py $NAMESPACE $CPU_NUM $EXEC_TRUE
	else
		# nothing to create but namespace
		echo "nothing to do except for namespace created !!"
	fi
}

get_opts ${@}

if [ $DELETE -eq 1 ]; then
	kubectl delete job/job-master -n $NAMESPACE
	kubectl delete --all pods --namespace=$NAMESPACE	
	kubectl delete --all svc --namespace=$NAMESPACE	
	exit 0
fi

# create namespace
kubectl create namespace $NAMESPACE

echo "Start generate YAML RS files..."
generate_rs_file
