import boto3
import json
import datetime
import csv
from operator import itemgetter

# Adjust the config below to get result that you need
DAYS_AGO = 0
START_TIME = datetime.datetime.now() - datetime.timedelta(days=DAYS_AGO)
REGION = 'eu-west-1'
INSTANCE_LIST = ['*']
SP_PAYMENT_OPTION = 'All Upfront'
SP_TYPE = 'Compute'
SP_PRODUCT = 'EC2'
SP_DURATION = 31536000
SP_TENANCY = 'shared'
SP_PRODUCT_DESCRIPTION = 'Linux/UNIX'
SPOT_PRODUCT_DESCRIPTION = 'Linux/UNIX (Amazon VPC)'
OD_PRODUCT = 'AmazonEC2'
OD_OS = 'Linux'
OD_TENANCY = 'Shared'
# Only show instance types when THRESHOLD_LOW < (Spot instance discount - Savings Plan discount) < THRESHOLD_HIGH
THRESHOLD_LOW = -100
THRESHOLD_HIGH = 100
OUTPUT_FILE = 'pricing.csv'

# Create boto3 clients
ec2_client = boto3.client('ec2', region_name=REGION)
savings_plans_client = boto3.client('savingsplans', region_name=REGION)
pricing_client = boto3.client('pricing', region_name='us-east-1')

# Get On Demand pricing list for instances
def get_on_demand_price_list():
    paginator = pricing_client.get_paginator('get_products')

    response_iterator = paginator.paginate(
        ServiceCode=OD_PRODUCT,
        Filters=[
            {
                'Type': 'TERM_MATCH',
                'Field': 'regionCode',
                'Value': REGION
            },
            {
                'Type': 'TERM_MATCH',
                'Field': 'capacitystatus',
                'Value': 'Used'
            },
            {
                'Type': 'TERM_MATCH',
                'Field': 'tenancy',
                'Value': OD_TENANCY
            },
            {
                'Type': 'TERM_MATCH',
                'Field': 'preInstalledSw',
                'Value': 'NA'
            },
            {
                'Type': 'TERM_MATCH',
                'Field': 'operatingSystem',
                'Value': OD_OS
            }
        ],
        PaginationConfig={
            'PageSize': 100
        }
    )

    price_list = {}
    for response in response_iterator:
        for priceItem in response['PriceList']:
            priceItemJson = json.loads(priceItem)
            #print(priceItemJson)

            for onDemandValues in priceItemJson['terms']['OnDemand'].keys():
                for priceDimensionValues in priceItemJson['terms']['OnDemand'][onDemandValues]['priceDimensions']:
                    instanceType = priceItemJson['product']['attributes']['instanceType']
                    instancePrice = priceItemJson['terms']['OnDemand'][onDemandValues]['priceDimensions'][priceDimensionValues]['pricePerUnit']['USD']

                    price_list[instanceType] = float(instancePrice)

    return(price_list)


# Get Savings Plans pricing list for instances
def get_savings_plans_price_list(instance_list):
    # Get the Savings Plans offering
    savings_plans_offers = savings_plans_client.describe_savings_plans_offerings(
        paymentOptions=[SP_PAYMENT_OPTION],
        planTypes=[SP_TYPE],
        productType=SP_PRODUCT,
        durations=[SP_DURATION]
    )
    
    # Get the Savings Plans pricing
    next_token = ''
    savings_plans_rates_list = []
    default_parameters = {
        'savingsPlanOfferingIds': [savings_plans_offers['searchResults'][0]['offeringId']],
        'savingsPlanPaymentOptions': [SP_PAYMENT_OPTION],
        'savingsPlanTypes': [SP_TYPE],
        'products': [SP_PRODUCT],
        'filters': [
            {'name': 'instanceType', 'values': instance_list},
            {'name': 'tenancy', 'values': [SP_TENANCY]},
            {'name': 'productDescription', 'values': [SP_PRODUCT_DESCRIPTION]},
            {'name': 'region', 'values': [REGION]}
        ]
    }
    
    while True:
        response = savings_plans_client.describe_savings_plans_offering_rates(**default_parameters)
    
        # Append the items from the current response to the list
        savings_plans_rates_list.extend(response['searchResults'])
        # If there are no more items, stop the loop
        if not response.get('nextToken'):
            break
        
        # Set the NextToken to retrieve the next page of items
        default_parameters['nextToken'] = response['nextToken']
    
    # Create a dictionary of instance types and their Savings Plans pricing
    savings_plans_dict = {}
    for savings_plan in savings_plans_rates_list:
        if savings_plan['savingsPlanOffering']['durationSeconds'] == SP_DURATION and 'BoxUsage' in savings_plan['usageType']:
            instance_type = savings_plan['properties'][2]['value']
            savings_plans_dict[instance_type] = savings_plan['rate']

    return savings_plans_dict


# Get Spot Instance pricing list for instances
def get_spot_instance_price_list(instance_list):
    # Call the describe_spot_price_history API for all instance types in the list 
    paginator = ec2_client.get_paginator('describe_spot_price_history')
    spot_prices = paginator.paginate(
        StartTime=START_TIME,
        EndTime=START_TIME,
        InstanceTypes=instance_list,
        ProductDescriptions=[SPOT_PRODUCT_DESCRIPTION]
    ).build_full_result()

    """ 
    spot_prices = ec2_client.describe_spot_price_history(
        StartTime=START_TIME,
        EndTime=START_TIME,
        InstanceTypes=instance_list,
        ProductDescriptions=[SPOT_PRODUCT_DESCRIPTION]
    )"""
    
    sorted_spot_prices = sorted(spot_prices['SpotPriceHistory'], key=itemgetter('InstanceType'))
    
    return sorted_spot_prices


# ----------------------------------- Main Handler --------------------------------------

# List all instance types as filtered
paginator = ec2_client.get_paginator('describe_instance_types')
instances = paginator.paginate(
    Filters=[{
        'Name': 'instance-type',
        'Values': INSTANCE_LIST
    }]
).build_full_result()

# Create instance list
instance_list = []
for instance in instances['InstanceTypes']:
    instance_list.append(instance['InstanceType'])
#print(len(instance_list))

# Get On Demand Price list for all instance types
on_demand_price_list = get_on_demand_price_list()
#print(len(on_demand_price_list))

# Get Savings Plans Price list for instances
savings_plans_price_list = get_savings_plans_price_list(instance_list)
#print(len(savings_plans_price_list))

# Get Spot Instance Price list for instances
spot_instance_price_list = get_spot_instance_price_list(instance_list)
#print(len(spot_instance_price_list))

# Compare On Demand, Spot and Savings Plans pricing and generate result list
header = ['Instance','AZ','OD Price','Spot Price','Spot %','SP Price','SP %','Diff %']
header_format = "%-15s %-12s %-10s %-10s %-10s %-10s %-10s %-10s"
result_list = []
for price in spot_instance_price_list:
    instance_type = price['InstanceType']
    spot_price = float(price['SpotPrice'])
    az = price['AvailabilityZone']
    if instance_type in savings_plans_price_list:
        savings_plans_price = float(savings_plans_price_list[instance_type])
        on_demand_price = on_demand_price_list[instance_type]
        spot_discount = round(((on_demand_price - spot_price) / on_demand_price) * 100, 2)
        savings_plans_discount = round(((on_demand_price - savings_plans_price) / on_demand_price) * 100, 2)
        discount_diff = round(spot_discount - savings_plans_discount,2)

        data = [instance_type,az,'$'+str(on_demand_price),'$'+str(spot_price),str(spot_discount)+'%','$'+str(savings_plans_price),str(savings_plans_discount)+'%',str(discount_diff)+'%']

        if THRESHOLD_LOW < discount_diff < THRESHOLD_HIGH:
            result_list.append(data)
    else:
        print(f"No Savings Plans pricing found for instance type {instance_type}")

# Print all results to screen
print(header_format % (header[0],header[1],header[2],header[3],header[4],header[5],header[6],header[7]))
for result in result_list:
    print(header_format % (result[0],result[1],result[2],result[3],result[4],result[5],result[6],result[7]))

# Export all results to csv file
with open(OUTPUT_FILE, 'w') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(header)
    for result in result_list:
        csv_writer.writerow(result)
