declare -a devs=("sda")
declare -a days=("02" "03" "04")
# declare -a days=("06")
declare -a hosts=("hera")
declare -a cpus=("all" "0" "1")
declare -a nics=("eth0" "eth1" "ovs-system" "eth2" "br0" "vlan1" "vlan110" "vlan120" "veth37iris" "lo" )

src_base="sysstat-files/sa"
dst_base="results"
dst_end=".csv"


for host in "${hosts[@]}"
do
    echo Processing $host!
    for day in "${days[@]}" 
    do 

        for dev in "${devs[@]}"
        do
            src_filename=./$host/$src_base"$day"
            dst_filename=./$host/$dst_base/$host-"$day"-io-$dev$dst_end

            if [ -e "${dst_filename}" ]
            then
                echo $dst_filename exists - skipping!
            else
                echo creating $dst_filename
                echo "00:00:01 dev rd_sec/s wr_sec/s avgrq-sz avgqu-sz await svctm %util" > $dst_filename
                sar -d -p -f $src_filename | grep " $dev " | tr -s ' ' | sed -e "s/,/./g" | head -n -2 >> $dst_filename
            fi 
        done

        src_filename=./$host/$src_base"$day"
        dst_filename=./$host/${dst_base}/$host-"$day"-cpu$dst_end

        if [ -e "${dst_filename}" ]
        then
            echo $dst_filename exists - skipping!
        else
            echo creating $dst_filename
            echo 00:00:01 CPU %user %nice %system %iowait %steal %idle > $dst_filename
            sar -u -f $src_filename | tr -s ' ' | sed -e "s/,/./g" | head -n -2 >> $dst_filename
        fi

        dst_filename="./diagrams/$host-"$day"-graphic-io.png"
        if [ -e "${dst_filename}" ]
        then
            echo Plot $dst_filename exists - skipping!
        else
            echo "Plotting data for day $day in file $dst_filename."
            gnuplot -e "host='$host'; dom='$day'; filename_plot='$dst_filename'"  ./$host/plot-io.pl
        fi   

        for cpu in "${cpus[@]}"
        do
            src_filename=./$host/$src_base"$day"
            dst_filename=./$host/${dst_base}/$host-"$day"-cpu-$cpu$dst_end

            if [ -e "${dst_filename}" ]
            then
                echo $dst_filename exists - skipping!
            else 
                echo creating $dst_filename
                echo "00:00:01 CPU %user %nice %system %iowait %steal %idle" > $dst_filename
                sar -P ALL -f $src_filename | tr -s ' ' | grep -E "^.{9}$cpu" | sed -e "s/,/./g" | head -n -2 >> $dst_filename
            fi
        done
       
        dst_filename="./diagrams/$host-"$day"-graphic-cpu-"$day".png"                             
        if [ -e "${dst_filename}" ]                                                  
        then                                                                         
            echo Plot $dst_filename exists - skipping!                               
        else                                                                         
            echo "Plotting data for day "$day" in file $dst_filename."                 
            gnuplot -e "host='$host'; dom='$day'; filename_plot='$dst_filename'"  ./$host/plot-cpu.pl
        fi


        for nic in "${nics[@]}"
        do
            src_filename=./$host/$src_base"$day"
            dst_filename=./$host/${dst_base}/$host-"$day"-nic-$nic$dst_end

            if [ -e "${dst_filename}" ]
            then
                echo $dst_filename exists - skipping!
            else
                echo creating $dst_filename
                echo "00:00:01 IFACE rxpck/s txpck/s rxkB/s txkB/s rxcmp/s txcmp/s rxmcst/s %ifutil" > $dst_filename
                sar -n DEV -f $src_filename | tr -s ' ' | grep -E "^.{9}$nic" | sed -e "s/,/./g" | head -n -2 >> $dst_filename
            fi
        done

        dst_filename="./diagrams/$host-"$day"-graphic-nic.png"                             
        if [ -e "${dst_filename}" ]                                                  
        then                                                                         
            echo Plot $dst_filename exists - skipping!                               
        else                                                                         
            echo "Plotting data for day "$day" in file $dst_filename."                 
            gnuplot -e "host='$host'; dom='$day'; filename_plot='$dst_filename'"  ./$host/plot-nic.pl
        fi

        src_filename=./$host/$src_base"$day"
        dst_filename=./$host/${dst_base}/$host-"$day"-memory$dst_end

        if [ -e "${dst_filename}" ]
        then
            echo $dst_filename exists - skipping!
        else
            echo creating $dst_filename
            echo "00:00:00    kbmemfree kbmemused  %memused kbbuffers  kbcached  kbcommit   %commit  kbactive   kbinact   kbdirty" > $dst_filename
            sar -r -f $src_filename | grep -v "kbmemfree\|^$\|Durchschn." | head -n -1 >> $dst_filename
        fi

        src_filename=./$host/$src_base"$day"
        dst_filename=./$host/${dst_base}/$host-"$day"-swap$dst_end

        if [ -e "${dst_filename}" ]
        then
            echo $dst_filename exists - skipping!
        else
            echo creating $dst_filename
            echo "00:00:00    kbswpfree kbswpused  %swpused  kbswpcad   %swpcad" > $dst_filename
            sar -S -f $src_filename | grep -v "kbswpfree\|^$\|Durchschn" | head -n -1 >> $dst_filename
        fi

        src_filename=./$host/$src_base"$day"
        dst_filename=./$host/${dst_base}/$host-"$day"-swap-pagesio$dst_end

        if [ -e "${dst_filename}" ]
        then
            echo $dst_filename exists - skipping!
        else
            echo creating $dst_filename
            echo "00:00:00     pgpgin/s pgpgout/s   fault/s  majflt/s  pgfree/s pgscank/s pgscand/s pgsteal/s    %vmeff" > $dst_filename
            sar -B -f $src_filename | grep -v "pgpgin\|Durchschn" | head -n -1 >> $dst_filename
        fi

        dst_filename="./diagrams/$host-"$day"-graphic-memory.png"                             
        if [ -e "${dst_filename}" ]                                                  
        then                                                                         
            echo Plot $dst_filename exists - skipping!                               
        else                                                                         
            echo "Plotting data for day "$day" in file $dst_filename."                 
            gnuplot -e "host='$host'; dom='$day'; filename_plot='$dst_filename'"  ./$host/plot-mem.pl
        fi

    done

done
