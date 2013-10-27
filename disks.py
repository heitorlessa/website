import ephemeral_disk
import os, urllib2

# Instantiate instance_tools class into ephemeral
ephemeral = ephemeral_disk.tools(force=1)

# Get the current instance type of the instance which run this script
instance_type = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-type').read()

# Create new SWAP primary partition with 8GB if ephemeral disk was replaced, also create /mnt partition and format it
ephemeral.create_disk_partition('/dev/xvdb', '8G', '1', instance_type)

# Format new partition as SWAP and enable it afterwards
ephemeral.enable_swap('/dev/xvdb1')

# Format new partition created as EXT4
ephemeral.format_as_ext4('/dev/xvdb2')

# Mount as /mnt the new partition
ephemeral.mount_partition('/dev/xvdb2', '/mnt')
