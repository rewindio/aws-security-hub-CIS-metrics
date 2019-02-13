# aws-security-hub-CIS-metrics

This repo contains a cloudformation template which will create all of the needed log filters, metrics and alarms to conform with the CIS framework used by AWS Security hub.

I've packaged these up in Cloudformation and based them on the [AWS quickstart example](https://github.com/aws-quickstart/quickstart-compliance-cis-benchmark/blob/master/templates/cis-benchmark.template).  It should be noted however that using the AWS quickstart will not work for Security hub because the metric filters do not exactly match that which is documented in the CIS document.  Security hub needs an exact match to flag a standard as being compliant.

# Using
* Configure Cloudtrail to send logs to a Cloudwatch log group as discussed in the Security Hub documentation
* Create a new SNS topic to send your alerts to. Subscribe either your email or use our [cloudwatch slack notifier](https://github.com/rewindio/aws-cloudwatch-slack-notifier)
* Create a new Cloudformation stack using the template in this repo.  You'll be prompted for the SNS Topic ARN and the name of the Cloudwatch logs group that Cloudtrail is logging to (ie. /aws/cloudtrail)

That should be it.  Note that security hub only checks for compliance with CIS standards every 12 hours so you will need to wait until the next check to make sure your new metric filters and alarms are detected correctly by Security Hub.