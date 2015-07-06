<% include('elements/monthly.html', #well, not really, daily flag below
                'title'        => $agentname.
                                  'Daily Sales, Credits and Receipts Summary',
                'items'        => \@items,
                'labels'       => \%label,
                'graph_labels' => \%graph_label,
                'colors'       => \%color,
                'links'        => \%link,
                'agentnum'     => $agentnum,
                'cust_classnum'=> \@classnums,
                'daily'        => 1,
                'start_day'    => $smday,
                'start_month'  => $smon+1,
                'start_year'   => $syear,
                'end_day'      => $emday,
                'end_month'    => $emon+1,
                'end_year'     => $eyear,
             )
%>
<%init>

die "access denied"
  unless $FS::CurrentUser::CurrentUser->access_right('Financial reports');

#XXX or virtual
my( $agentnum, $agent ) = ('', '');
if ( $cgi->param('agentnum') =~ /^(\d+)$/ ) {
  $agentnum = $1;
  $agent = qsearchs('agent', { 'agentnum' => $agentnum } );
  die "agentnum $agentnum not found!" unless $agent;
}

my $agentname = $agent ? $agent->agent.' ' : '';

my @classnums;
if ( $cgi->param('cust_classnum') ) {
  @classnums = grep /^\d+$/, $cgi->param('cust_classnum');
}

my($beginning, $ending) = FS::UI::Web::parse_beginning_ending($cgi);
my ($ssec,$smin,$shour,$smday,$smon,$syear,$swday,$syday,$sisdst) 
    = localtime($beginning);
my ($esec,$emin,$ehour,$emday,$emon,$eyear,$ewday,$eyday,$eisdst) 
    = localtime($ending);

my @items = ($cgi->param('exclude_discount') ? 'invoiced' : 'gross');
push @items,
            qw( discounted netsales
                credits  netcredits
                payments receipts
                refunds  netrefunds
                cashflow netcashflow
              );

my %label = (
  'gross'       => 'Gross Sales',
  'invoiced'    => 'Invoiced Sales',
  'netsales'    =>   'Net Sales',
  'discounted'  => 'Discounts',
  'credits'     => 'Gross Credits',
  'netcredits'  =>   'Net Credits',
  'payments'    => 'Gross Receipts',
  'receipts'    =>   'Net Receipts',
  'refunds'     => 'Gross Refunds',
  'netrefunds'  =>   'Net Refunds',
  'cashflow'    => 'Gross Cashflow',
  'netcashflow' =>   'Net Cashflow',
);

my %graph_suffix = (
 'gross'       => ' (invoiced + discounts)',
 'invoiced'    => '',
 'netsales'    => ' (invoiced - applied credits)',
 'discounted'  => '',
 'credits'     => ' (credited)',
 'netcredits'  => ' (applied credits)',
 'payments'    => ' (payments)',
 'receipts'    => ' (applied payments)',
 'refunds'     => ' (refunds)',
 'netrefunds'  => ' (applied refunds)',
 'cashflow'    => ' (payments - refunds)',
 'netcashflow' => ' (applied payments - applied refunds)',
);
my %graph_label = map { $_ => $label{$_}.$graph_suffix{$_} } keys %label;

my %color = (
  'gross'       => '9999ff', #light blue
  'invoiced'    => '9999ff', #light blue
  'netsales'    => '0000cc', #blue
  'credits'     => 'ff9999', #light red
  'netcredits'  => 'cc0000', #red
  'payments'    => '99cc99', #light green
  'receipts'    => '00cc00', #green
  'refunds'     => 'ffcc99', #light orange
  'netrefunds'  => 'ff9900', #orange
  'cashflow'    => '99cc33', #light olive
  'netcashflow' => '339900', #olive
  'discounted'  => 'cc33cc', #purple-ish?
);

my %link = (
  'gross'      => "${p}search/cust_bill.html?agentnum=$agentnum;",
  'invoiced'   => "${p}search/cust_bill.html?agentnum=$agentnum;invoiced=1;",
  'netsales'   => "${p}search/cust_bill.html?agentnum=$agentnum;net=1;",
  'credits'    => "${p}search/cust_credit.html?agentnum=$agentnum;",
  'netcredits' => "${p}search/cust_credit_bill.html?agentnum=$agentnum;",
  'payments'   => "${p}search/cust_pay.html?magic=_date;agentnum=$agentnum;",
  'receipts'   => "${p}search/cust_bill_pay.html?agentnum=$agentnum;",
  'refunds'    => "${p}search/cust_refund.html?magic=_date;agentnum=$agentnum;",
  'netrefunds' => "${p}search/cust_credit_refund.html?agentnum=$agentnum;",
  'discounted' => "${p}search/cust_bill_pkg_discount.html?agentnum=$agentnum;",
);

</%init>
