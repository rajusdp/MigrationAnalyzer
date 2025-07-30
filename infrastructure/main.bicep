// Main Bicep template for Slack-to-Teams Migration Estimator
// Deploys all required Azure resources for production deployment

targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Resource token for unique resource naming')
param resourceToken string = toLower(uniqueString(subscription().id, environmentName, location))

@description('App Service Plan SKU')
@allowed(['B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1V2', 'P2V2', 'P3V2'])
param appServicePlanSku string = 'B2'

@description('PostgreSQL Server SKU')
@allowed(['Standard_B1ms', 'Standard_B2s', 'Standard_D2s_v3', 'Standard_D4s_v3'])
param postgreSqlSku string = 'Standard_B2s'

@description('PostgreSQL Database name')
param databaseName string = 'migration_estimator'

@description('Administrator username for PostgreSQL')
param postgresAdminUsername string = 'pgadmin'

@secure()
@description('Administrator password for PostgreSQL')
param postgresAdminPassword string

@description('Application Insights location')
param appInsightsLocation string = location

// Variables
var abbrs = loadJsonContent('./abbreviations.json')
var resourceNamePrefix = '${abbrs.resourceGroup}${environmentName}-${resourceToken}'

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${resourceNamePrefix}'
  location: location
  tags: {
    'azd-env-name': environmentName
    'environment': environmentName
    'project': 'migration-estimator'
  }
}

// Key Vault for storing secrets
module keyVault './modules/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// Storage Account for blob storage
module storage './modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    containerNames: ['migration-reports', 'file-uploads']
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// Log Analytics Workspace
module logAnalytics './modules/loganalytics.bicep' = {
  name: 'loganalytics'
  scope: rg
  params: {
    name: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// Application Insights
module appInsights './modules/appinsights.bicep' = {
  name: 'appinsights'
  scope: rg
  params: {
    name: '${abbrs.insightsComponents}${resourceToken}'
    location: appInsightsLocation
    workspaceResourceId: logAnalytics.outputs.id
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// PostgreSQL Flexible Server
module postgres './modules/postgres.bicep' = {
  name: 'postgres'
  scope: rg
  params: {
    name: '${abbrs.dBforPostgreSQLServers}${resourceToken}'
    location: location
    sku: postgreSqlSku
    databaseName: databaseName
    administratorLogin: postgresAdminUsername
    administratorLoginPassword: postgresAdminPassword
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// Redis Cache
module redis './modules/redis.bicep' = {
  name: 'redis'
  scope: rg
  params: {
    name: '${abbrs.cacheRedis}${resourceToken}'
    location: location
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// App Service Plan
module appServicePlan './modules/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: rg
  params: {
    name: '${abbrs.webServerFarms}${resourceToken}'
    location: location
    sku: appServicePlanSku
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// Backend API App Service
module backendApp './modules/appservice.bicep' = {
  name: 'backend'
  scope: rg
  params: {
    name: '${abbrs.webSitesAppService}backend-${resourceToken}'
    location: location
    appServicePlanId: appServicePlan.outputs.id
    appInsightsConnectionString: appInsights.outputs.connectionString
    runtimeName: 'python'
    runtimeVersion: '3.11'
    appSettings: {
      DATABASE_URL: 'postgresql://${postgresAdminUsername}:${postgresAdminPassword}@${postgres.outputs.fqdn}:5432/${databaseName}'
      REDIS_URL: redis.outputs.connectionString
      AZURE_STORAGE_CONNECTION_STRING: storage.outputs.connectionString
      APPLICATION_INSIGHTS_KEY: appInsights.outputs.instrumentationKey
      JWT_SECRET_KEY: '@Microsoft.KeyVault(VaultName=${keyVault.outputs.name};SecretName=jwt-secret-key)'
      ENVIRONMENT: environmentName
    }
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// Frontend App Service
module frontendApp './modules/appservice.bicep' = {
  name: 'frontend'
  scope: rg
  params: {
    name: '${abbrs.webSitesAppService}frontend-${resourceToken}'
    location: location
    appServicePlanId: appServicePlan.outputs.id
    appInsightsConnectionString: appInsights.outputs.connectionString
    runtimeName: 'node'
    runtimeVersion: '18-lts'
    appSettings: {
      NEXT_PUBLIC_API_BASE_URL: 'https://${backendApp.outputs.defaultHostName}/api'
      NEXT_PUBLIC_AZURE_CLIENT_ID: '@Microsoft.KeyVault(VaultName=${keyVault.outputs.name};SecretName=azure-client-id)'
      NEXT_PUBLIC_AZURE_AUTHORITY: '@Microsoft.KeyVault(VaultName=${keyVault.outputs.name};SecretName=azure-authority)'
      NODE_ENV: 'production'
    }
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// Azure Front Door for CDN and SSL
module frontDoor './modules/frontdoor.bicep' = {
  name: 'frontdoor'
  scope: rg
  params: {
    name: '${abbrs.networkFrontDoors}${resourceToken}'
    backendHostName: backendApp.outputs.defaultHostName
    frontendHostName: frontendApp.outputs.defaultHostName
    tags: {
      'azd-env-name': environmentName
    }
  }
}

// Store secrets in Key Vault
resource jwtSecretKey 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  name: '${keyVault.outputs.name}/jwt-secret-key'
  properties: {
    value: uniqueString(resourceGroup().id, 'jwt-secret')
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name

output API_BASE_URL string = 'https://${backendApp.outputs.defaultHostName}'
output WEB_BASE_URL string = 'https://${frontendApp.outputs.defaultHostName}'
output FRONTEND_URL string = 'https://${frontDoor.outputs.frontDoorEndpointHostName}'

output AZURE_STORAGE_ACCOUNT string = storage.outputs.name
output AZURE_STORAGE_CONNECTION_STRING string = storage.outputs.connectionString

output POSTGRES_HOST string = postgres.outputs.fqdn
output POSTGRES_DATABASE string = databaseName
output POSTGRES_USERNAME string = postgresAdminUsername

output REDIS_HOST string = redis.outputs.hostName
output REDIS_PORT string = redis.outputs.sslPort

output KEY_VAULT_NAME string = keyVault.outputs.name
output APPLICATION_INSIGHTS_KEY string = appInsights.outputs.instrumentationKey
