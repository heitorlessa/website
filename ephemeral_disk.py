#-------------------------------------------------------------------------------
# Name:        Ephemeral Python
# Purpose:     Quick module for AWS Article regarding Ephemeral disks
#
# Author:      Heitor Lessa
# Company:     www.heitorlessa.com
#
# Created:     26/10/2013
# License:     GPL - Fell free to change and distribute
#
# NOTES:
#-------------------------------------------------------------------------------

import os
import logging
from sys import exit

## Define logging properties globally as will be used over all code.
logging.basicConfig(level=logging.INFO, format='Timestamp: %(asctime)s - Level: %(levelname)s - %(message)s')


class tools:
    """ This class will provide some useful functions to manage
        EC2 instance resources"""

    def __init__(self, force=0):
        """ Force parameter can be enabled when you are sure
            that existing partitions can be deleted while you
            are trying to create new ones. This also
            applies for mount_points that can be forced to be
            unmounted

            Example:

            t = ephemeral_python.tools(force=1)
            t.create_disk_partition('/dev/xvdb', '1', 'c1.medium')

        """
        self.force = force

    def create_disk_partition(self, disk, size, part_number, *instances):
        """ Creates a partition using fdisk using the information given.

            Example:

            create_disk_partition('/dev/xvdj', '8G', '1')

            This will create the first primary partition in /dev/xvdj
            with 8GB size.

            This function only creates primary partitions as
            ephemeral disk is a spare disk and there is no need
            to create logical partitions.

            This function can also be used to create ephemeral SWAP partition
            and also create another partition (usually for /mnt) using
            the space left. It calculates only one ephemeral disk based
            on instance type.

            create_disk_partition('/dev/xvdj', '8G', '1', 'c1.medium')

            This will create a SWAP of 8G + /mnt of 327G as total of the ephemeral
            disk is 335 for a c1.medium instance.
            """

        # fdisk command to create partition
        command = """echo "
n
p
{2}

+{1}
w
" | /sbin/fdisk {0} 1>/dev/null """
        partitioning = command.format(disk, size, part_number)
        partition = "".join((disk, part_number))
        try:
            # Check if partition number is between 1 and 4
            if not int(part_number) in range(1,5):
                logging.error('Partition number must be between 1 and 4')
                exit(2)

            if not self.force:
                # Check if partition selected exist, otherwise raise an error
                # Hint: module commands or subprocess can be used here to simplify
                if self.check_partition(partition):
                    logging.error('Partition {0} already exist, please choose other one'.format(partition))
                    logging.error('Set "force=1" while instantiating this class to force removing existing partitions')
                    exit(2)
            else:
                count = 1
                ## Loop through all primary partitions and delete if found
                for attempts in range(1,5):
                    my_part = disk + str(count)
                    if self.check_partition(my_part):
                        self.delete_disk_partition(disk, str(count))

                    # Jump to the next partition
                    count = count + 1

            # Partprobe is needed to reload Disk partition table on Linux as it is required in few cases
            logging.info('Reloading Disk partition table')
            os.system("partprobe")

            # Check if partition size ends with G, otherwise raise an error
            if not size.endswith('G'):
                logging.error('Partitions size must be in Gigabytes (e.g 9G, 10G)')
                exit(2)

            # Check if any instance type was given as an argument
            # and then create the ephemeral partition (/mnt), otherwise
            # do nothing.
            for instance in instances:
                if instance is not None:
                    self.create_ephemeral_partition(disk, size, instance)

            logging.info('Creating partition...!')
            os.system(partitioning)

            # Partprobe is needed to reload Disk partition table on Linux as it is required in few cases
            os.system("partprobe")

            # Confirm if partition was created successfully
            if not self.check_partition(partition):
                logging.critical('Could not create the partition. Maybe the size is too big?')
                exit(2)

            logging.info('Partition created successfully')

        except:
            logging.critical("Error trying to create a new partition")
            exit(2)

    def create_ephemeral_partition(self, disk, size, instance):
        """ If an instance type was given to create_disk_partition function,
            then this function will be called informing the primary partition size
            and the instance type, therefore this function will calculate the space left
            to create /mnt partition (Amazon ONLY). Example:

            create_ephemeral_partition('/dev/xvdb', '8G', 'c1.medium')

            Please be aware that these numbers can change, therefore
            a method to update these values would be useful in the future
            """

        if 'm1.small' in instance:
            total = 140
        if 'c1.medium' in instance:
            total = 335
        if 'm1.medium' in instance:
            total = 390
        if 'm1.large' in instance:
            total = 410
        if 'm2.xlarge' in instance:
            total = 410
        if 'm2.2xlarge' in instance:
            total = 840
        if 'm2.4xlarge' in instance:
            total = 830
        if 'c1.xlarge' in instance:
            total = 410
        if 'cc1.4xlarge' in instance:
            total = 830
        if 'cc2.8xlarge' in instance:
            total = 830
        if 'cg1.4xlarge' in instance:
            total = 830
        if 'cr1.8xlarge' in instance:
            total = 230
        if 'hi1.4xlarge' in instance:
            total = 830
        if 'hs1.8xlarge' in instance:
            total = 1014


        # Calculates how large ephemeral partition can be
        # Then, it creates itself using all space left
        eph = total - int(size.strip('G'))
        mnt = "".join((str(eph), 'G'))

        # Confirm what partition number is available to create
        ### Create loop here to confirm what part number can be used
        self.create_disk_partition(disk, mnt, '2')

    def check_partition(self, partition):
        """ Check if partition exists and return True or False """

        # Confirm that fdisk binary exists
        if not self.check_command('/sbin/fdisk'):
            logging.error('fdisk command does not exist or cannot be accessible')
            exit(2)

        # Ensure that partition in question already exist or not
        # Then, it returns True or False depending on the result
        if partition in os.popen("fdisk -l {0} 2> /dev/null".format(partition)).read():
            return True
        else:
            return False

    def check_mount_point(self, partition):
        """ Check if partition is mounted, example:

        check_mount_point('/dev/xvdj1')

            Return True or False depending on the result.
            However it force is enabled, it tries to unmount
        """
        try:

            # Check if partition exists before enabling SWAP
            if not self.check_partition(partition):
                logging.error('Partition {0} does not exist, please choose an existent one'.format(partition))
                exit(2)

            # Confirm that mount/umount binary exists
            if not self.check_command('/bin/mount') and not self.check_command('/bin/umount'):
                logging.error('mount/umount command does not exist or cannot be accessible')
                exit(2)

            # Ensure that partition in question is already mounted or not
            # Returns True or False depending on the result
            # It is also important to check if is mounted as SWAP which uses a different place

            mount_points = os.popen("mount 2> /dev/null".format(partition)).read()
            with open('/proc/swaps', 'r') as filename:
                swap_points = filename.read()
                if partition in mount_points or partition in swap_points:
                    return True
                elif partition[:-1] in mount_points or partition[:-1] in swap_points:
                    return True
                else:
                    return False

        except:
            logging.error("Error while checking mount point")

    def check_command(self, command):
        """ Check if command exists and can be executed.access

            Returns True or False depending on the result
        """

        if os.path.isfile(command) and os.access(command, os.X_OK):
            return True
        else:
            return False

    def delete_disk_partition(self, disk, part_number):
        """ Delete partitions using fdisk, example:

        delete('/dev/xvdj', '1')

            Then, deletes partition 1 of the
            disk /dev/xvdj. """

        # fdisk command to delete partition
        command = """echo "
d
{1}
w
" | /sbin/fdisk {0} 1>/dev/null """
        partitioning = command.format(disk, part_number)
        partition = "".join((disk, part_number))
        try:
            # Check if partition number is between 1 and 4
            if not part_number in str(partition):
                logging.error('Partition number must be between 1 and 4')
                exit(2)

            # Check if partition selected exist, otherwise raise an error
            if not self.check_partition(partition):
                logging.error('Partition {0} does not exist, please choose an existent one'.format(partition))
                exit(2)

            logging.info("Deleting partition... !")
            os.system(partitioning)
            logging.info("Partition deleted successfully")

        except:
            logging.error('Error while deleting disk partition {0} - Please double check if it is in use and try again'.format(partition))

    def enable_swap(self, partition):
        """ Enable SWAP partition previously created, example:

        enable('/dev/xvdj1')

            Then, formats partition as SWAP and then enable
            using SWAPON command in Linux"""
        try:

            # Check if partition exists before enabling SWAP
            if not self.check_partition(partition):
                logging.error('Partition {0} does not exist, please choose an existent one'.format(partition))
                exit(2)

            # Confirm that mkswap binary exists
            if not self.check_command('/sbin/mkswap'):
                logging.error('mkswap command does not exist or cannot be accessible')
                exit(2)

            # Double check if partition is already in use
            # and if Force is set unmount it before taking any action
            if self.check_mount_point(partition):
                if self.force:
                    self.force_unmount(partition)
                else:
                    logging.error('Partition {0} already mounted, cannot touch it!'.format(partition))
                    exit(2)

            # Creates SWAP using mkswap and enable it using swapon
            logging.info('Formating partition {0} as SWAP'.format(partition))
            os.system("mkswap {0} 1>/dev/null".format(partition))

            os.system('swapon {0} 1>/dev/null'.format(partition))
            logging.info('SWAP enabled successfully')

        except:
            logging.error("Error while enabling SWAP")

    def disable_swap(self, partition):
        """ Disable SWAP partition, example

        disable('/dev/xvdj1') """

        try:
            # Check if partition exists before enabling SWAP
            if not self.check_partition(partition):
                logging.error('Partition {0} does not exist, please choose an existent one'.format(partition))
                exit(2)

             # Confirm that swapoff binary exists
            if not self.check_command('/sbin/swapoff'):
                logging.error('swapoff command does not exist or cannot be accessible')
                exit(2)

            # Double check if partition is already in use
            # and if Force is set unmount it before taking any action
            if self.check_mount_point(partition):
                if self.force:
                    self.force_unmount(partition)
                else:
                    logging.error('Partition {0} already mounted, cannot touch it!'.format(partition))
                    exit(2)

            os.system("swapoff {0} 1>/dev/null".format(partition))
            logging.info('SWAP disabled successfully')

        except:
            logging.error("Error while disabling SWAP")

    def format_as_ext3(self, partition):
        """ Format partition previously created as EXT3, example:

        format_as_ext3('/dev/xvdj1')
        """

        try:
            # Check if partition selected exist, otherwise raise an error
            if not self.check_partition(partition):
                logging.error('Partition {0} does not exist, please choose an existent one'.format(partition))
                exit(2)

             # Confirm that mkfs.ext3 binary exists
            if not self.check_command('/sbin/mkfs.ext3'):
                logging.error('mkfs.ext3 command does not exist or cannot be accessible')
                exit(2)

            # Double check if partition is already in use
            # and if Force is set unmount it before taking any action
            if self.check_mount_point(partition):
                if self.force:
                    self.force_unmount(partition)
                else:
                    logging.error('Partition {0} already mounted, cannot touch it!'.format(partition))
                    exit(2)

            logging.info('Formating partition {0} as EXT3'.format(partition))

            os.system("mkfs.ext3 -q {0} 1>/dev/null".format(partition))
            logging.info('Partition formatted successfully as EXT3')

        except:
            logging.error("Error while formatting partition as EXT3")

    def format_as_ext4(self, partition):
        """ Format partition previously created as EXT4, example:

        format_as_ext4('/dev/xvdj1')
        """

        try:
            # Check if partition selected exist, otherwise raise an error
            if not self.check_partition(partition):
                logging.error('Partition {0} does not exist, please choose an existent one'.format(partition))
                exit(2)

             # Confirm that mkfs.ext4 binary exists
            if not self.check_command('/sbin/mkfs.ext4'):
                logging.error('mkfs.ext4 command does not exist or cannot be accessible')
                exit(2)

            # Double check if partition is already in use
            # and if Force is set unmount it before taking any action
            if self.check_mount_point(partition):
                if self.force:
                    self.force_unmount(partition)
                else:
                    logging.error('Partition {0} already mounted, cannot touch it!'.format(partition))
                    exit(2)

            logging.info('Formating partition {0} as EXT4'.format(partition))

            os.system("mkfs.ext4 -q {0} 1>/dev/null".format(partition))
            logging.info('Partition formmatted successfully as EXT4')

        except:
            logging.error("Error while formatting partition as EXT4")

    def mount_partition(self, partition, mount_point):
        """ Mount partition previously created and formatted, example:

        mount_partition('/dev/xvdj2', '/mnt')
        """

        try:
            # Check if partition selected exist, otherwise raise an error
            if not self.check_partition(partition):
                logging.error('Partition {0} does not exist, please choose an existent one'.format(partition))
                exit(2)

             # Confirm that mount binary exists
            if not self.check_command('/bin/mount'):
                logging.error('mount command does not exist or cannot be accessible, please ensure you also have permission to mount')
                exit(2)

            # Double check if partition is already in use
            # and if Force is set unmount it before taking any action
            if self.check_mount_point(partition):
                if self.force:
                    self.force_unmount(partition)
                else:
                    logging.error('Partition {0} already mounted, cannot touch it!'.format(partition))
                    exit(2)

            logging.info('Mounting partition {0} in {1}'.format(partition, mount_point))

            if os.system("mount {0} {1} 1>/dev/null".format(partition, mount_point)):
                logging.info('Partition {0} was mounted successfully in {1}'.format(partition, mount_point))


        except:
            logging.error("Error while mounting partition {0} in {1}".format(partition, mount_point))

    def force_unmount(self, partition):
        """ Force unmount partition once mounted

        force_unmount('/dev/xvdb1') or force_unmount('/dev/xvdb)

        """

        if self.force:
            # Check if partition selected exist, otherwise raise an error
            # Hint: module commands or subprocess can be used here to simplify
            if not self.check_partition(partition):
                logging.error('Partition {0} does not exist, please choose an existing one'.format(partition))
                exit(2)

            logging.info("Unmounting file system")
            for attempts in range(1,4):
                # Check if full partition or entire disk is mounted
                # Then umounts if true (swap and or FS)
                # This can be improved confirming if it is SWAP or FS rather than using both commands
                if self.check_mount_point(partition):
                    os.system("umount -l {0} 2>/dev/null".format(partition))
                    os.system("swapoff {0} 2>/dev/null".format(partition))
                elif self.check_mount_point(partition[:-1]):
                    os.system("umount -l {0} 2>/dev/null".format(partition[:-1]))
                    os.system("swapoff {0} 2>/dev/null".format(partition[:-1]))
                else:
                    # Break the loop If unmounted successfully otherwise try again
                    logging.info('Unmounted sucessfully!')
                    break
