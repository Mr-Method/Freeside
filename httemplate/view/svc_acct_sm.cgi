<%
#
# $Id: svc_acct_sm.cgi,v 1.1 2001-07-30 07:36:04 ivan Exp $
#
# Usage: svc_acct_sm.cgi svcnum
#        http://server.name/path/svc_acct_sm.cgi?svcnum
#
# based on view/svc_acct.cgi
# 
# ivan@voicenet.com 97-jan-5
#
# added navigation bar
# ivan@voicenet.com 97-jan-30
# 
# rewrite ivan@sisd.com 98-mar-15
#
# Changes to allow page to work at a relative position in server
#       bmccane@maxbaud.net     98-apr-3
#
# /var/spool/freeside/conf/domain ivan@sisd.com 98-jul-17
#
# $Log: svc_acct_sm.cgi,v $
# Revision 1.1  2001-07-30 07:36:04  ivan
# templates!!!
#
# Revision 1.11  2000/07/17 10:58:42  ivan
# better error messages if svc_acct or svc_domain records are missing
#
# Revision 1.10  1999/04/08 12:00:19  ivan
# aesthetic update
#
# Revision 1.9  1999/02/28 00:04:03  ivan
# removed misleading comments
#
# Revision 1.8  1999/02/09 09:23:00  ivan
# visual and bugfixes
#
# Revision 1.7  1999/02/07 09:59:42  ivan
# more mod_perl fixes, and bugfixes Peter Wemm sent via email
#
# Revision 1.6  1999/01/19 05:14:22  ivan
# for mod_perl: no more top-level my() variables; use vars instead
# also the last s/create/new/;
#
# Revision 1.5  1999/01/18 09:41:46  ivan
# all $cgi->header calls now include ( '-expires' => 'now' ) for mod_perl
# (good idea anyway)
#
# Revision 1.4  1998/12/23 03:09:52  ivan
# $cgi->keywords instead of $cgi->query_string
#
# Revision 1.3  1998/12/17 09:57:24  ivan
# s/CGI::(Base|Request)/CGI.pm/;
#
# Revision 1.2  1998/12/16 05:24:30  ivan
# use FS::Conf;
#

use strict;
use vars qw($conf $cgi $mydomain $query $svcnum $svc_acct_sm $cust_svc
            $pkgnum $cust_pkg $custnum $part_svc $p $domsvc $domuid $domuser
            $svc $svc_domain $domain $svc_acct $username );
use CGI;
use FS::UID qw(cgisuidsetup);
use FS::CGI qw(header popurl menubar );
use FS::Record qw(qsearchs);
use FS::Conf;
use FS::svc_acct_sm;
use FS::cust_svc;
use FS::cust_pkg;
use FS::part_svc;
use FS::svc_domain;
use FS::svc_acct;

$cgi = new CGI;
cgisuidsetup($cgi);

$conf = new FS::Conf;
$mydomain = $conf->config('domain');

($query) = $cgi->keywords;
$query =~ /^(\d+)$/;
$svcnum = $1;
$svc_acct_sm = qsearchs('svc_acct_sm',{'svcnum'=>$svcnum});
die "Unknown svcnum" unless $svc_acct_sm;

$cust_svc = qsearchs('cust_svc',{'svcnum'=>$svcnum});
$pkgnum = $cust_svc->getfield('pkgnum');
if ($pkgnum) {
  $cust_pkg=qsearchs('cust_pkg',{'pkgnum'=>$pkgnum});
  $custnum=$cust_pkg->getfield('custnum');
} else {
  $cust_pkg = '';
  $custnum = '';
}

$part_svc = qsearchs('part_svc',{'svcpart'=> $cust_svc->svcpart } )
  or die "Unkonwn svcpart";

$p = popurl(2);
print $cgi->header( '-expires' => 'now' ), header('Mail Alias View', menubar(
  ( ( $pkgnum || $custnum )
    ? ( "View this package (#$pkgnum)" => "${p}view/cust_pkg.cgi?$pkgnum",
        "View this customer (#$custnum)" => "${p}view/cust_main.cgi?$custnum",
      )
    : ( "Cancel this (unaudited) account" =>
          "${p}misc/cancel-unaudited.cgi?$svcnum" )
  ),
  "Main menu" => $p,
));

($domsvc,$domuid,$domuser) = (
  $svc_acct_sm->domsvc,
  $svc_acct_sm->domuid,
  $svc_acct_sm->domuser,
);
$svc = $part_svc->svc;
$svc_domain = qsearchs('svc_domain',{'svcnum'=>$domsvc})
  or die "Corrupted database: no svc_domain.svcnum matching domsvc $domsvc";
$domain = $svc_domain->domain;
$svc_acct = qsearchs('svc_acct',{'uid'=>$domuid})
  or die "Corrupted database: no svc_acct.uid matching domuid $domuid";
$username = $svc_acct->username;

print qq!<A HREF="${p}edit/svc_acct_sm.cgi?$svcnum">Edit this information</A>!,
      "<BR>Service #$svcnum",
      "<BR>Service: <B>$svc</B>",
      qq!<BR>Mail to <B>!, ( ($domuser eq '*') ? "<I>(anything)</I>" : $domuser ) , qq!</B>\@<B>$domain</B> forwards to <B>$username</B>\@$mydomain mailbox.!,
      '</BODY></HTML>'
;

%>
