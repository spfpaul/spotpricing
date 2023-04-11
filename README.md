# Spot and Savings Plans Pricing comparision tool

## Description
This tool is used to list instance types by comparing Spot pricing and Savings Plans pricing.

## Sample Output
Sample output as below:
```
Instance        AZ           OD Price   Spot Price Spot %     SP Price   SP %       Diff %
a1.4xlarge      eu-west-1a   $0.4608    $0.1988    56.86%     $0.3381    26.63%     30.23%
a1.4xlarge      eu-west-1b   $0.4608    $0.2389    48.16%     $0.3381    26.63%     21.53%
a1.xlarge       eu-west-1b   $0.1152    $0.0572    50.35%     $0.0845    26.65%     23.7% 
c1.medium       eu-west-1b   $0.148     $0.0167    88.72%     $0.109     26.35%     62.37%
c1.medium       eu-west-1a   $0.148     $0.0171    88.45%     $0.109     26.35%     62.1% 
c1.xlarge       eu-west-1c   $0.592     $0.1624    72.57%     $0.439     25.84%     46.73%
c3.4xlarge      eu-west-1c   $0.956     $0.4664    51.21%     $0.705     26.26%     24.95%
c3.4xlarge      eu-west-1b   $0.956     $0.4594    51.95%     $0.705     26.26%     25.69%
c3.large        eu-west-1a   $0.12      $0.0526    56.17%     $0.088     26.67%     29.5% 
c4.4xlarge      eu-west-1b   $0.905     $0.4276    52.75%     $0.667     26.3%      26.45%
c4.8xlarge      eu-west-1b   $1.811     $0.8783    51.5%      $1.334     26.34%     25.16%
c4.8xlarge      eu-west-1a   $1.811     $0.9474    47.69%     $1.334     26.34%     21.35%
c4.large        eu-west-1b   $0.113     $0.0599    46.99%     $0.083     26.55%     20.44%
c5.12xlarge     eu-west-1b   $2.304     $1.088     52.78%     $1.703     26.09%     26.69%
```
Fields explained as below:
```
Instance: instance type
AZ: Availability Zone
OD Price: On Demand pricing
Spot Price: Spot instance pricing
SP %: Savings Plans discount comparing to On Demand instances
Spot %: Spot instance discount comparing to On Demand 
SP Price: Savings Plans pricing
SP %: Savings Plans discount comparing to On Demand instances
Diff %: Difference between Spot instance discount and Savings Plans discount
```

## Usage
Command:
```
python3 spot_pricing.py
```
Note: This command also generate CSV file as defined.

## Support
None

## Roadmap
None

## Contribution and Acknowledgments
None

## License
None

## Project status
None