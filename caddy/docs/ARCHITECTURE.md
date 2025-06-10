# Caddy JWT Authentication System Architecture

## System Overview Diagram

```mermaid
graph TB
    %% User and Browser
    User[👤 User] --> Browser[🌐 Browser]

    %% Caddy Proxy Layer
    Browser --> Caddy[🔧 Caddy Reverse Proxy<br/>Port 8000/8001]

    %% Authentication Flow
    Caddy -->|forward_auth request| AuthCheck{🔐 Auth Check<br/>/auth/verify}
    AuthCheck -->|No JWT cookie| AuthFail[❌ 401 Unauthorized]
    AuthCheck -->|Valid JWT| AuthSuccess[✅ 200 OK + Headers]

    %% Auth Service
    AuthCheck --> CatkinAuth[🐱 Catkin Auth Service<br/>Port 5000]
    AuthFail -->|Redirect| LoginPage[📝 Login Page<br/>/auth/login]
    LoginPage --> CatkinAuth

    %% Database
    CatkinAuth --> Database[(🗄️ PostgreSQL<br/>User Data & OAuth)]

    %% JWT Processing
    CatkinAuth -->|Generate| JWT[🎫 JWT Token<br/>HS256, 24h expiry]
    JWT -->|Set as HttpOnly cookie| Browser

    %% Protected Services
    AuthSuccess -->|Proxy with headers| ProtectedApp1[🛡️ Protected App 1<br/>Port 8080]
    AuthSuccess -->|Proxy with headers| ProtectedApp2[🛡️ Admin Panel<br/>Port 9000]

    %% Headers passed to apps
    AuthSuccess -.->|X-User-Email<br/>X-User-ID<br/>X-Auth-Method| HeaderFlow[📤 User Headers]
    HeaderFlow --> ProtectedApp1
    HeaderFlow --> ProtectedApp2

    %% OAuth Integration
    LoginPage -->|OAuth login| OAuth[🔗 OAuth Providers<br/>GitHub, Google, Frappe]
    OAuth --> CatkinAuth

    %% Health Check
    Caddy -->|No auth required| HealthCheck[💚 /health endpoint]

    %% Styling
    classDef userStyle fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef proxyStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef authStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef appStyle fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef dataStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class User,Browser userStyle
    class Caddy proxyStyle
    class CatkinAuth,AuthCheck,JWT,LoginPage,OAuth authStyle
    class ProtectedApp1,ProtectedApp2,HealthCheck appStyle
    class Database dataStyle
```

## Configuration Flow

```mermaid
flowchart TD
    %% Configuration Files
    DevConfig[📄 Caddyfile<br/>Development]
    ProdConfig[📄 Caddyfile.production<br/>Production]
    DockerConfig[🐳 docker-compose.yml]

    %% Caddy Configuration Sections
    DevConfig --> GlobalOpts[🌐 Global Options<br/>auto_https off]
    DevConfig --> AuthProxy[🔗 Auth Service Proxy<br/>handle /auth/*]
    DevConfig --> ForwardAuth[🔐 Forward Auth<br/>forward_auth directive]
    DevConfig --> AppProxy[📱 App Proxy<br/>reverse_proxy to apps]
    DevConfig --> ErrorHandle[❌ Error Handling<br/>401 → login redirect]
    DevConfig --> HealthEndpoint[💚 Health Check<br/>no auth required]

    %% Production additions
    ProdConfig --> HTTPS[🔒 HTTPS Auto-certs]
    ProdConfig --> SecurityHeaders[🛡️ Security Headers<br/>CSP, HSTS, etc.]

    %% Docker Setup
    DockerConfig --> CatkinService[🐱 Catkin Service<br/>Port 5000]
    DockerConfig --> PostgresService[🗄️ PostgreSQL<br/>Port 5432]
    DockerConfig --> DemoApps[🎭 Demo Apps<br/>Ports 8080, 9000]

    %% Flow connections
    ForwardAuth -.->|Validates with| AuthProxy
    AppProxy -.->|Protected by| ForwardAuth
    ErrorHandle -.->|Redirects to| AuthProxy

    classDef configStyle fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px
    classDef serviceStyle fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef securityStyle fill:#fff8e1,stroke:#f57f17,stroke-width:2px

    class DevConfig,ProdConfig,DockerConfig configStyle
    class CatkinService,PostgresService,DemoApps serviceStyle
    class ForwardAuth,SecurityHeaders,HTTPS,ErrorHandle securityStyle
```

## Data Flow Architecture

```mermaid
graph LR
    %% Input/Output
    Request[📥 HTTP Request] --> CaddyProcess{🔧 Caddy Processing}

    %% Caddy Decision Tree
    CaddyProcess -->|/auth/*| AuthService[🐱 Catkin Auth Service]
    CaddyProcess -->|/health| HealthResponse[💚 Health OK]
    CaddyProcess -->|Protected paths| AuthValidation{🔐 JWT Validation}

    %% Authentication paths
    AuthValidation -->|No cookie| LoginRedirect[↩️ Redirect to Login]
    AuthValidation -->|Invalid JWT| Unauthorized[❌ 401 Unauthorized]
    AuthValidation -->|Valid JWT| AddHeaders[📤 Add User Headers]

    %% Success flow
    AddHeaders --> ProxyToApp[📡 Proxy to Protected App]
    ProxyToApp --> AppResponse[📤 App Response]

    %% Response paths
    AuthService --> Response[📤 HTTP Response]
    HealthResponse --> Response
    LoginRedirect --> Response
    Unauthorized --> Response
    AppResponse --> Response

    %% Data stores
    AuthService -.->|Read/Write| UserData[(👥 User Database)]
    AuthService -.->|Read| OAuthConfig[(🔗 OAuth Config)]

    %% Headers detail
    AddHeaders -.->|X-User-Email<br/>X-User-ID<br/>X-Auth-Method| HeaderDetail[📋 Header Details]

    classDef processStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef authStyle fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef dataStyle fill:#e0f2f1,stroke:#4caf50,stroke-width:2px
    classDef errorStyle fill:#ffebee,stroke:#f44336,stroke-width:2px

    class CaddyProcess,ProxyToApp processStyle
    class AuthValidation,AddHeaders,AuthService authStyle
    class UserData,OAuthConfig,HeaderDetail dataStyle
    class LoginRedirect,Unauthorized errorStyle
```

## Production Deployment Architecture

```mermaid
graph TB
    %% External Layer
    Internet[🌍 Internet] --> LoadBalancer[⚖️ Load Balancer]

    %% CDN/Edge
    LoadBalancer --> CDN[🚀 CDN/Edge Cache]

    %% Application Layer
    CDN --> CaddyProd[🔧 Caddy Production<br/>HTTPS + Security Headers]

    %% SSL/TLS
    CaddyProd -.->|Auto-cert| LetsEncrypt[🔒 Let's Encrypt]

    %% Authentication Layer
    CaddyProd -->|forward_auth| AuthCluster[🐱 Catkin Auth Cluster]
    AuthCluster --> AuthDB[(🗄️ PostgreSQL Primary)]
    AuthDB -.-> AuthDBReplica[(📚 PostgreSQL Replica)]

    %% Application Clusters
    CaddyProd -->|Protected traffic| AppCluster1[🛡️ App Cluster 1]
    CaddyProd -->|Protected traffic| AppCluster2[🛡️ App Cluster 2]

    %% Service Discovery
    AppCluster1 --> ServiceDiscovery[🔍 Service Discovery]
    AppCluster2 --> ServiceDiscovery
    AuthCluster --> ServiceDiscovery

    %% Monitoring
    CaddyProd -.->|Metrics| Monitoring[📊 Monitoring]
    AuthCluster -.->|Metrics| Monitoring
    AppCluster1 -.->|Metrics| Monitoring
    AppCluster2 -.->|Metrics| Monitoring

    %% Logging
    CaddyProd -.->|Logs| LogAggregation[📝 Log Aggregation]
    AuthCluster -.->|Logs| LogAggregation

    %% Secrets Management
    AuthCluster -.->|JWT Secret| SecretManager[🔐 Secret Manager]
    AuthDB -.->|DB Credentials| SecretManager

    %% Backup
    AuthDB -.->|Backup| Backup[💾 Backup Storage]

    classDef infraStyle fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef securityStyle fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef appStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef dataStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef monitorStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px

    class Internet,LoadBalancer,CDN,ServiceDiscovery infraStyle
    class CaddyProd,LetsEncrypt,SecretManager securityStyle
    class AuthCluster,AppCluster1,AppCluster2 appStyle
    class AuthDB,AuthDBReplica,Backup dataStyle
    class Monitoring,LogAggregation monitorStyle
```

---

### Before Caddy: Unsecured Service Architecture

```mermaid
graph TB
    %% Direct access problems
    User[👤 User] --> Browser[🌐 Browser]
    Browser -->|Direct access| UnsecuredApp1[❌ Unsecured App 1<br/>Port 8080]
    Browser -->|Direct access| UnsecuredApp2[❌ Unsecured App 2<br/>Port 9000]

    %% Authentication exists but isolated
    Browser -.->|Separate login| CatkinAuth[🐱 Catkin Auth<br/>Port 5000]
    CatkinAuth -.->|Manual session check| Database[(🗄️ Database)]

    %% Problems highlighted
    UnsecuredApp1 -.->|❌ No auth check| Security1[🚨 Security Gap 1]
    UnsecuredApp2 -.->|❌ No auth check| Security2[🚨 Security Gap 2]

    Browser -.->|❌ Multiple logins| LoginProblem[🔄 Session Management Hell]
    UnsecuredApp1 -.->|❌ No user context| Context1[❓ Who is this user?]
    UnsecuredApp2 -.->|❌ No user context| Context2[❓ Who is this user?]

    %% Port management nightmare
    Browser -.->|🔗 Remember port 8080| PortProblem1[😤 Port Management]
    Browser -.->|🔗 Remember port 9000| PortProblem2[😤 Port Management]
    Browser -.->|🔗 Remember port 5000| PortProblem3[😤 Port Management]

    classDef problemStyle fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef unsecuredStyle fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef userStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class Security1,Security2,LoginProblem,Context1,Context2,PortProblem1,PortProblem2,PortProblem3 problemStyle
    class UnsecuredApp1,UnsecuredApp2 unsecuredStyle
    class User,Browser userStyle
```

### After Caddy: Unified Secure Gateway

```mermaid
graph TB
    %% Single entry point
    User[👤 User] --> Browser[🌐 Browser]
    Browser -->|Single domain/port| Caddy[✅ Caddy Gateway<br/>Port 8000]

    %% Centralized authentication
    Caddy -->|forward_auth| CatkinAuth[🐱 Catkin Auth<br/>Port 5000]
    CatkinAuth --> Database[(🗄️ Database)]

    %% Protected services
    Caddy -->|✅ Authenticated proxy| SecuredApp1[🛡️ Secured App 1<br/>Port 8080]
    Caddy -->|✅ Authenticated proxy| SecuredApp2[🛡️ Secured App 2<br/>Port 9000]

    %% Solutions highlighted
    Caddy -.->|✅ Single login| SolutionAuth[🔐 Centralized Auth]
    Caddy -.->|✅ User context| SolutionContext[👤 X-User-Email headers]
    Caddy -.->|✅ Hidden complexity| SolutionPorts[🌐 Single endpoint]
    Caddy -.->|✅ HTTPS/Security| SolutionSecurity[🔒 Auto-TLS + Headers]

    classDef solutionStyle fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
    classDef securedStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef gatewayStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px

    class SolutionAuth,SolutionContext,SolutionPorts,SolutionSecurity solutionStyle
    class SecuredApp1,SecuredApp2 securedStyle
    class Caddy gatewayStyle
```

### Configuration Complexity Reduction

```mermaid
graph LR
    %% Before: Complex configuration per service
    subgraph "Before: Per-Service Configuration"
        App1Config[App 1 Config<br/>❌ Manual auth checks<br/>❌ Session management<br/>❌ CORS handling<br/>❌ HTTPS setup]
        App2Config[App 2 Config<br/>❌ Duplicate auth logic<br/>❌ User context parsing<br/>❌ Security headers<br/>❌ Certificate management]
        AuthConfig[Auth Service<br/>❌ Multiple session stores<br/>❌ CORS for each app<br/>❌ Token validation endpoints]
    end

    %% After: Single configuration
    subgraph "After: Centralized Caddy Configuration"
        SingleConfig[Caddyfile<br/>✅ forward_auth once<br/>✅ Automatic headers<br/>✅ Auto HTTPS<br/>✅ Security headers<br/>✅ Error handling]
    end

    %% Developer experience
    BeforeWork[👨‍💻 Developer Work<br/>❌ Configure auth per service<br/>❌ Manage multiple sessions<br/>❌ Handle CORS everywhere<br/>❌ Debug auth issues per app]

    AfterWork[👨‍💻 Developer Work<br/>✅ Configure once in Caddy<br/>✅ Apps receive user headers<br/>✅ Focus on business logic<br/>✅ Consistent error handling]

    App1Config --> BeforeWork
    App2Config --> BeforeWork
    AuthConfig --> BeforeWork

    SingleConfig --> AfterWork

    classDef beforeStyle fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    classDef afterStyle fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class App1Config,App2Config,AuthConfig,BeforeWork beforeStyle
    class SingleConfig,AfterWork afterStyle
```
