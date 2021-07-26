#! /bin/bash

function show_help
{
 echo -e "This script loads the (reduced) memcached trace keys and generates a PCAP."
 echo -e "Example: ./generate_pcap.sh -i <INPUT_DIRECTORY> -o <OUTPUT_DIRECTORY>"
 echo -e "\t\t-i <INPUT_DIRECTORY>: Directory containing the (reduced) memcached trace keys."
 echo -e "\t\t-o <OUTPUT_DIRECTORY>: Directory to contain the resulting PCAP files. Cannot be the same with INPUT_DIRECTORY."
 echo -e "\t\t-r Enabling this flag clears the existing progress file and processing of the directory will start from scratch."
 exit
 }

while getopts "h?i:o:r" opt
 do
 	case "$opt" in
 	h|\?)
 		show_help
 		;;
 	i)
 		input_directory=$OPTARG
 		;;
 	o)
 		output_directory=$OPTARG
 		;;
	r)
 		reset=1
 		;;
 	*)
 		show_help
 		;;
 	esac
done

if [ -z $input_directory ]
then
  echo -e "No INPUT_DIRECTORY is set!"
  show_help
fi
if [ -z $output_directory ]
then
  echo -e "No OUTPUT_DIRECTORY is set!"
  show_help
fi

if [ $input_directory == $output_directory ]
then 
	echo -e "INPUT_DIRECTORY cannot be the same with OUTPUT_DIRECTORY!"
fi

if [ ! -d $output_directory ] 
then
	mkdir $output_directory
fi

traces=`ls $input_directory`

if [ ! -z $reset ]
then
	echo -n "" > $output_directory/progress
fi

if [ ! -f $output_directory/progress ]
then
	touch $output_directory/progress
fi

for trace in $traces
do
	if grep $trace $output_directory/progress > /dev/null 
	then
		echo "Skipping $input_directory/$trace ..."
	else
		echo "Currently processing $input_directory/$trace ..."
		awk '{ printf "payload=0001%08x00000000\n", $1 }' $input_directory/$trace > /tmp/tmp.csv
		echo "Writing PCAP file ..."
		./pcap_generator_from_csv.py -i /tmp/tmp.csv -o $output_directory/$trace > /dev/null
		if [$? -eq 0 ]
		then  
			echo $trace >> $output_directory/progress
		else
			echo -e "An error has occured! Terminating the script..." 
			exit 1
		fi
	fi
done



# for i in $(cat tmp/sample.out); do printf 'payload=0001%08x00000000\n' $i >> tmp.csv; done