package FS::part_export::vpopmail;

use vars qw(@ISA @saltset $exportdir $rsync $ssh);
use File::Path;
use FS::UID qw( datasrc );
use FS::part_export;

@ISA = qw(FS::part_export);

@saltset = ( 'a'..'z' , 'A'..'Z' , '0'..'9' , '.' , '/' );

$rsync = "rsync";
$ssh = "ssh";

sub rebless { shift; }

sub _export_insert {
  my($self, $svc_acct) = (shift, shift);
  $self->vpopmail_queue( $svc_acct->svcnum, 'insert',
    $svc_acct->username,
    crypt($svc_acct->_password,$saltset[int(rand(64))].$saltset[int(rand(64))]),
    $svc_acct->domain,
  );
}

sub _export_replace {
  my( $self, $new, $old ) = (shift, shift, shift);

  my $cpassword = crypt(
    $new->_password, $saltset[int(rand(64))].$saltset[int(rand(64))]
  );

  return "can't change username with vpopmail"
    if $old->username ne $new->username;

  #no.... if mail can't be preserved, better to disallow username changes
  #if ($old->username ne $new->username || $old->domain ne $new->domain ) {
  #  vpopmail_queue( $svc_acct->svcnum, 'delete', 
  #    $old->username, $old->domain
  #  );
  #  vpopmail_queue( $svc_acct->svcnum, 'insert', 
  #    $new->username,
  #    $cpassword,
  #    $new->domain,
  #  );

  return '' unless $old->_password ne $new->_password;

  $self->vpopmail_queue( $new->svcnum, 'replace',
    $new->username, $cpassword, $new->domain );
}

sub _export_delete {
  my( $self, $svc_acct ) = (shift, shift);
  $self->vpopmail_queue( $svc_acct->svcnum, 'delete',
    $svc_acct->username, $svc_acct->domain );
}

#a good idea to queue anything that could fail or take any time
sub vpopmail_queue {
  my( $self, $svcnum, $method ) = (shift, shift, shift);
  my $exportdir = "/usr/local/etc/freeside/export." . datasrc;
  my $queue = new FS::queue {
    'svcnum' => $svcnum,
    'job'    => "FS::part_export::vpopmail::vpopmail_$method",
  };
  $queue->insert(
    $exportdir,
    $self->option('machine'),
    $self->option('dir'),
    $self->option('uid'),
    $self->option('gid'),
    @_
  );
}

sub vpopmail_insert { #subroutine, not method
  my( $exportdir, $machine, $dir, $uid, $gid ) = splice @_,0,5;
  my( $username, $password, $domain ) = @_;
  
  (open(VPASSWD, ">>$exportdir/domains/$domain/vpasswd")
    and flock(VPASSWD,LOCK_EX)
  ) or die "can't open vpasswd file for $username\@$domain: ".
           "$exportdir/domains/$domain/vpasswd: $!";
  print VPASSWD join(":",
    $username,
    $password,
    '1',
    '0',
    $username,
    "$dir/domains/$domain/$username",
    'NOQUOTA',
  ), "\n";

  flock(VPASSWD,LOCK_UN);
  close(VPASSWD);

  for my $mkdir (
    map { "$exportdir/domains/$domain/$username$_" }
      ( '', qw( /Maildir /Maildir/cur /Maildir/new /Maildir/tmp ) )
  ) {
    mkdir $mkdir, 0700 or die "can't mkdir $mkdir: $!";
  }

  vpopmail_sync( $exportdir, $machine, $dir, $uid, $gid );

}

sub vpopmail_replace { #subroutine, not method
  my( $exportdir, $machine, $dir, $uid, $gid ) = splice @_,0,5;
  my( $username, $password, $domain ) = @_;
  
  (open(VPASSWD, "$exportdir/domains/$domain/vpasswd")
    and flock(VPASSWD,LOCK_EX)
  ) or die "can't open $exportdir/domains/$domain/vpasswd: $!";

  open(VPASSWDTMP, ">$exportdir/domains/$domain/vpasswd.tmp")
    or die "Can't open $exportdir/domains/$domain/vpasswd.tmp: $!";

  while (<VPASSWD>) {
    my ($mailbox, $pw, @rest) = split(':', $_);
    print VPASSWDTMP $_ unless $username eq $mailbox;
    print VPASSWDTMP join (':', ($mailbox, $password, @rest))
      if $username eq $mailbox;
  }

  close(VPASSWDTMP);

  rename "$exportdir/domains/$domain/vpasswd.tmp", "$exportdir/domains/$domain/vpasswd"
    or die "Can't rename $exportdir/domains/$domain/vpasswd.tmp: $!";

  flock(VPASSWD,LOCK_UN);
  close(VPASSWD);

  vpopmail_sync( $exportdir, $machine, $dir, $uid, $gid );

}

sub vpopmail_delete { #subroutine, not method
  my( $exportdir, $machine, $dir, $uid, $gid ) = splice @_,0,5;
  my( $username, $domain ) = @_;
  
  (open(VPASSWD, "$exportdir/domains/$domain/vpasswd")
    and flock(VPASSWD,LOCK_EX)
  ) or die "can't open $exportdir/domains/$domain/vpasswd: $!";

  open(VPASSWDTMP, ">$exportdir/domains/$domain/vpasswd.tmp")
    or die "Can't open $exportdir/domains/$domain/vpasswd.tmp: $!";

  while (<VPASSWD>) {
    my ($mailbox, $rest) = split(':', $_);
    print VPASSWDTMP $_ unless $username eq $mailbox;
  }

  close(VPASSWDTMP);

  rename "$exportdir/domains/$domain/vpasswd.tmp",
         "$exportdir/domains/$domain/vpasswd"
    or die "Can't rename $exportdir/domains/$domain/vpasswd.tmp: $!";

  flock(VPASSWD,LOCK_UN);
  close(VPASSWD);

  rmtree "$exportdir/domains/$domain/$username"
    or die "can't rmtree $exportdir/domains/$domain/$username: $!";

  vpopmail_sync( $exportdir, $machine, $dir, $uid, $gid );
}

sub vpopmail_sync {
  my( $exportdir, $machine, $dir, $uid, $gid ) = splice @_,0,5;
  
  chdir $exportdir;
  my @args = ( $rsync, "-rlpt", "-e", $ssh, "domains/",
               "vpopmail\@$machine:$dir/domains/"  );
  system {$args[0]} @args;
}


