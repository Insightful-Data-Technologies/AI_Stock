# Fix DNS Configuration for aizevinstocks.com

## Current Problem:
- Domain shows SSL certificate error
- DNS is using A records instead of CNAME
- Pointing to wrong IP addresses

## DNS Records to Update in GoDaddy:

### DELETE Current A Records:
- Type: A, Name: @, Value: 15.197.225.128 ❌
- Type: A, Name: @, Value: 3.33.251.168 ❌

### ADD New CNAME Record:
- Type: CNAME
- Name: @
- Value: victorious-smoke-01f2b7f0f.3.azurestaticapps.net
- TTL: 1 Hour

### Optional - Add www subdomain:
- Type: CNAME  
- Name: www
- Value: victorious-smoke-01f2b7f0f.3.azurestaticapps.net
- TTL: 1 Hour

## Steps:
1. Login to GoDaddy DNS Management
2. Delete the current A records
3. Add the CNAME record as shown above
4. Wait 5-10 minutes for DNS propagation
5. Azure will automatically provision SSL certificate

## After DNS Update:
- https://aizevinstocks.com will work with SSL
- Azure will show your custom domain in the portal
- No more certificate errors