HL Website Repo
=======

This Repo will be used only for python files described in website articles (usually about AWS or any automation related), so please feel free to download and use the code provided. Also, this will be intended to be a short summary when multiple files are added,
then README file will be placed with the file.

[ephemeral_disk.py]
-------

Handles disk partitions for ephemeral disks, but can be used with any other as well. 

You can easily install using setup.py provided:

<pre><code> python setup.py install</code></pre>

Then, you can try importing it to confirm if everything went fine:

<pre><code> import ephemeral_disk</code></pre>


Please find below a real example of how it can be used (you can use disks.py to get started):

<pre><code>ephemeral = ephemeral_disk.tools(force=1)</code></pre>

Here we instantiate the class using force attribute, which means that any existing partitions can be removed (BE CAREFUL HERE, only use if you know what you're doing),
which in turn can be useful when you launch a new instance from an AMI and ephemeral disk will be mounted by default in /mnt,
so if force is not enabled, our partitioning will fail as the disk is currently in use.

<pre><code>
# Get the current instance type of the instance which run this script
instance_type = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-type').read()
</code></pre>

where instance_type variable will store the value of the current instance type got from AWS Meta-data

<pre><code>
# Create a primary partition in '/dev/xvdb' disk with 8G
ephemeral.create_disk_partition('/dev/xvdb', '8G', '1', instance_type)
</code></pre>

As we are specifying what instance_type we are currently using, create_disk_partition method will calculate the space left
from a list (hardcoded, this can be improved) and then creating a second paritition ('/dev/xvdb2') with a single call, rather
than calling the method twice for example:

ephemeral.create_disk_partition('/dev/xvdb', '8G', '1')
ephemeral.create_disk_partition('/dev/xvdb', '300G', '2')

This is only useful when you want something more specific (i.e 3 partitions with different sizes for example), but in this case all we want
is to have 8G of SWAP and everything else be mounted in '/mnt'.

<pre><code>
# Format new partition as SWAP and enable it
ephemeral.enable_swap('/dev/xvdb1')
</code></pre>

Proceeding, we are now enabling our primary partition as SWAP...

<pre><code>
# Pretty obvious ;) Formatting the second partition created previously
ephemeral.format_as_ext4('/dev/xvdb2')
</code></pre>

Same as before but using EXT4 File system to our secondary partition.

<pre><code>
# Mount as /mnt the new partition
ephemeral.mount_partition('/dev/xvdb2', '/mnt')
</code></pre>

Mount partition given to a specific mount point, which in this case is our secondary partition onto '/mnt' :)

From here, you can do whatever you want like creating folders for backup, caching, sessions, etc.

All code is commented, so you can obtain help using help(method) for more information while coding.


Use case??
-----
 You have an Auto Scaling group where you launch instances up and down, but SWAP is not there, so rather than using a EBS volume for SWAP
 you can start using your ephemeral disk, partition it, format and use whatever you want \ o /
 
 Of course you will find several other useful ways for this.

