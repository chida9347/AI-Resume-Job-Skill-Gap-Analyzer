"""Versioned, auditable skill taxonomy.

Design rules
------------
* Canonical names are lower-case, stable identifiers used by the API.
* Aliases are matched with word boundaries (``java`` never matches ``javascript``).
* Distinct products stay distinct (PostgreSQL, MySQL and SQLite are not "SQL").
* ``related`` powers *partial* matches; it never proves a skill.
* ``implies`` is used only for defensible containment (PostgreSQL demonstrates SQL).

Add new skills here and cover them with a test in ``tests/test_matching.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Skill:
    name: str
    display: str
    category: str
    aliases: tuple[str, ...]
    related: tuple[str, ...] = ()
    implies: tuple[str, ...] = ()
    # Short/ambiguous aliases are matched case-sensitively in their natural casing.
    case_sensitive_aliases: tuple[str, ...] = field(default_factory=tuple)


def _s(
    name: str,
    display: str,
    category: str,
    aliases: list[str] | tuple[str, ...],
    related: list[str] | tuple[str, ...] = (),
    implies: list[str] | tuple[str, ...] = (),
    case_sensitive: list[str] | tuple[str, ...] = (),
    include_name: bool = True,
) -> Skill:
    all_aliases = [name, *aliases] if include_name else list(aliases)
    return Skill(
        name=name,
        display=display,
        category=category,
        aliases=tuple(dict.fromkeys(all_aliases)),
        related=tuple(related),
        implies=tuple(implies),
        case_sensitive_aliases=tuple(case_sensitive),
    )


_PROGRAMMING = "Programming Languages"
_FRONTEND = "Frontend"
_BACKEND = "Backend"
_DATABASE = "Databases"
_CLOUD = "Cloud & DevOps"
_DATA = "Data & ML"
_TESTING = "Testing & Security"
_TOOLS = "Tools & Practices"
_SOFT = "Soft Skills"
_BUSINESS = "Business & Product"
_CS = "CS Fundamentals"

SKILL_TAXONOMY: tuple[Skill, ...] = (
    # Programming languages
    _s("python", "Python", _PROGRAMMING, ["python3", "python 3"], ["pandas", "fastapi", "django"]),
    _s("javascript", "JavaScript", _PROGRAMMING, ["js", "ecmascript", "es6"], ["typescript", "react", "node.js"]),
    _s("typescript", "TypeScript", _PROGRAMMING, ["ts"], ["javascript", "react"], ["javascript"]),
    _s("java", "Java", _PROGRAMMING, ["java 8", "java 11", "java 17", "java 21"], ["spring boot", "kotlin"]),
    _s("c++", "C++", _PROGRAMMING, ["cpp", "c plus plus"], ["c", "rust"], case_sensitive=["C++"]),
    _s("c#", "C#", _PROGRAMMING, ["csharp", "c sharp"], [".net", "java"], case_sensitive=["C#"]),
    _s("go", "Go", _PROGRAMMING, ["golang", "go language", "Go"], ["rust", "python"], case_sensitive=["Go"], include_name=False),
    _s("rust", "Rust", _PROGRAMMING, ["rustlang"], ["c++", "go"], case_sensitive=["Rust"]),
    _s("ruby", "Ruby", _PROGRAMMING, ["ruby on rails", "rails"], ["python", "javascript"]),
    _s("php", "PHP", _PROGRAMMING, ["laravel"], ["javascript", "sql"]),
    _s("kotlin", "Kotlin", _PROGRAMMING, ["kotlin/android"], ["java", "swift"]),
    _s("swift", "Swift", _PROGRAMMING, ["swiftui"], ["kotlin", "objective-c"]),
    _s("scala", "Scala", _PROGRAMMING, ["scala 2", "scala 3"], ["java", "spark"]),
    _s("r", "R", _PROGRAMMING, ["r language", "rstudio", "R"], ["statistics", "python"], case_sensitive=["R"], include_name=False),
    _s("matlab", "MATLAB", _PROGRAMMING, ["simulink"], ["python", "statistics"]),
    _s("bash", "Bash", _PROGRAMMING, ["shell scripting", "shell script", "zsh"], ["linux", "powershell"]),
    _s("powershell", "PowerShell", _PROGRAMMING, ["pwsh"], ["bash", "windows server"]),
    _s("sql", "SQL", _PROGRAMMING, ["structured query language"], ["postgresql", "mysql", "sqlite"]),
    _s("solidity", "Solidity", _PROGRAMMING, ["smart contracts"], ["blockchain", "javascript"]),
    # Frontend
    _s("react", "React", _FRONTEND, ["react.js", "reactjs", "react 18", "react 19"], ["javascript", "next.js", "redux"], ["javascript"]),
    _s("next.js", "Next.js", _FRONTEND, ["nextjs", "next js"], ["react", "typescript"], ["react"]),
    _s("vue.js", "Vue.js", _FRONTEND, ["vue", "vuejs", "vue 3"], ["javascript", "nuxt.js"]),
    _s("angular", "Angular", _FRONTEND, ["angularjs", "angular 2"], ["typescript", "rxjs"]),
    _s("svelte", "Svelte", _FRONTEND, ["sveltekit"], ["javascript", "vue.js"]),
    _s("redux", "Redux", _FRONTEND, ["redux toolkit", "rtk"], ["react", "state management"]),
    _s("html", "HTML", _FRONTEND, ["html5"], ["css", "accessibility"]),
    _s("css", "CSS", _FRONTEND, ["css3", "cascading style sheets"], ["html", "sass", "tailwind css"]),
    _s("sass", "Sass/SCSS", _FRONTEND, ["scss", "sass"], ["css"]),
    _s("tailwind css", "Tailwind CSS", _FRONTEND, ["tailwind", "tailwindcss"], ["css"]),
    _s("bootstrap", "Bootstrap", _FRONTEND, ["bootstrap 5"], ["css"]),
    _s("material ui", "Material UI", _FRONTEND, ["mui", "material-ui"], ["react", "css"]),
    _s("webpack", "Webpack", _FRONTEND, ["webpack 5"], ["javascript", "vite"]),
    _s("vite", "Vite", _FRONTEND, ["vitejs"], ["javascript", "webpack"]),
    _s("responsive design", "Responsive Design", _FRONTEND, ["responsive web design", "mobile-first design"], ["css", "accessibility"]),
    _s("accessibility", "Accessibility", _FRONTEND, ["a11y", "wcag", "accessibility standards"], ["html", "responsive design"]),
    _s("figma", "Figma", _FRONTEND, ["figma design"], ["ui design", "ux design"]),
    _s("ui design", "UI Design", _FRONTEND, ["user interface design", "ui/ux"], ["ux design", "figma"]),
    _s("ux design", "UX Design", _FRONTEND, ["user experience design", "ux research"], ["ui design", "figma"]),
    _s("state management", "State Management", _FRONTEND, ["state management library"], ["redux", "react"]),
    # Backend
    _s("node.js", "Node.js", _BACKEND, ["nodejs", "node js", "node"], ["javascript", "express.js"], ["javascript"]),
    _s("express.js", "Express.js", _BACKEND, ["express", "expressjs"], ["node.js", "rest apis"]),
    _s("fastapi", "FastAPI", _BACKEND, ["fast api"], ["python", "rest apis"]),
    _s("django", "Django", _BACKEND, ["django rest framework", "drf"], ["python", "rest apis"]),
    _s("flask", "Flask", _BACKEND, ["flask api"], ["python", "rest apis"]),
    _s("spring boot", "Spring Boot", _BACKEND, ["spring framework", "spring mvc"], ["java", "rest apis"]),
    _s(".net", ".NET", _BACKEND, ["dotnet", "asp.net", "asp.net core"], ["c#", "rest apis"]),
    _s("graphql", "GraphQL", _BACKEND, ["apollo graphql", "graph ql"], ["rest apis", "api design"]),
    _s("rest apis", "REST APIs", _BACKEND, ["rest api", "restful api", "restful apis", "restful services"], ["api design", "http"]),
    _s("grpc", "gRPC", _BACKEND, ["grpc api"], ["rest apis", "api design"]),
    _s("microservices", "Microservices", _BACKEND, ["microservice architecture", "micro services"], ["distributed systems", "api design"]),
    _s("websockets", "WebSockets", _BACKEND, ["websocket", "socket.io"], ["http", "realtime systems"]),
    _s("celery", "Celery", _BACKEND, ["celery tasks"], ["python", "rabbitmq"]),
    _s("rabbitmq", "RabbitMQ", _BACKEND, ["rabbit mq"], ["kafka", "message queues"]),
    _s("kafka", "Apache Kafka", _BACKEND, ["apache kafka", "kafka streams"], ["rabbitmq", "message queues"]),
    _s("message queues", "Message Queues", _BACKEND, ["message queue", "message broker"], ["kafka", "rabbitmq"]),
    _s("api design", "API Design", _BACKEND, ["api architecture", "api development"], ["rest apis", "graphql"]),
    _s("http", "HTTP", _BACKEND, ["https", "http/2"], ["rest apis", "computer networks"]),
    _s("authentication", "Authentication", _BACKEND, ["authn", "login systems"], ["oauth", "jwt", "security"]),
    _s("oauth", "OAuth", _BACKEND, ["oauth2", "oauth 2.0", "openid connect", "oidc"], ["authentication", "jwt"]),
    _s("jwt", "JWT", _BACKEND, ["json web token", "json web tokens"], ["authentication", "oauth"]),
    _s("caching", "Caching", _BACKEND, ["cache", "caching strategy"], ["redis", "performance optimization"]),
    _s("background jobs", "Background Jobs", _BACKEND, ["job queue", "worker queue", "async tasks"], ["celery", "message queues"]),
    # Databases
    _s("postgresql", "PostgreSQL", _DATABASE, ["postgres", "psql", "pgsql"], ["sql", "mysql", "sqlite"], ["sql"]),
    _s("mysql", "MySQL", _DATABASE, ["mariadb"], ["sql", "postgresql"], ["sql"]),
    _s("sqlite", "SQLite", _DATABASE, ["sqlite3"], ["sql", "postgresql"], ["sql"]),
    _s("mongodb", "MongoDB", _DATABASE, ["mongo", "mongoose"], ["nosql", "database design"]),
    _s("redis", "Redis", _DATABASE, ["redis cache", "redis cluster"], ["caching", "memcached"]),
    _s("elasticsearch", "Elasticsearch", _DATABASE, ["elastic search", "opensearch"], ["search", "mongodb"]),
    _s("dynamodb", "DynamoDB", _DATABASE, ["dynamo db", "amazon dynamodb"], ["aws", "nosql"]),
    _s("cassandra", "Cassandra", _DATABASE, ["apache cassandra"], ["nosql", "database design"]),
    _s("oracle database", "Oracle Database", _DATABASE, ["oracle db", "oracle sql", "pl/sql"], ["sql", "postgresql"], ["sql"]),
    _s("sql server", "SQL Server", _DATABASE, ["microsoft sql server", "mssql", "t-sql"], ["sql", "postgresql"], ["sql"]),
    _s("supabase", "Supabase", _DATABASE, ["supabase auth"], ["postgresql", "firebase"]),
    _s("firebase", "Firebase", _DATABASE, ["firestore", "firebase auth"], ["nosql", "supabase"]),
    _s("nosql", "NoSQL", _DATABASE, ["non-relational database", "document database"], ["mongodb", "database design"]),
    _s("database design", "Database Design", _DATABASE, ["schema design", "data modeling", "database modeling"], ["sql", "normalization"]),
    _s("normalization", "Normalization", _DATABASE, ["database normalization"], ["database design", "sql"]),
    _s("orm", "ORM", _DATABASE, ["object relational mapping", "sqlalchemy", "hibernate", "prisma"], ["database design", "sql"]),
    # Cloud & DevOps
    _s("aws", "AWS", _CLOUD, ["amazon web services", "amazon aws"], ["azure", "gcp", "cloud computing"]),
    _s("azure", "Azure", _CLOUD, ["microsoft azure", "azure cloud"], ["aws", "gcp", "cloud computing"]),
    _s("gcp", "Google Cloud", _CLOUD, ["google cloud platform", "google cloud"], ["aws", "azure", "cloud computing"]),
    _s("cloud computing", "Cloud Computing", _CLOUD, ["cloud infrastructure", "cloud services"], ["aws", "azure", "gcp"]),
    _s("docker", "Docker", _CLOUD, ["dockerfile", "docker compose", "containerization", "containers"], ["kubernetes", "devops"]),
    _s("kubernetes", "Kubernetes", _CLOUD, ["k8s", "helm", "eks", "aks", "gke"], ["docker", "devops"]),
    _s("terraform", "Terraform", _CLOUD, ["infrastructure as code", "iac", "terraform cloud"], ["aws", "devops"]),
    _s("ansible", "Ansible", _CLOUD, ["ansible playbook"], ["terraform", "devops"]),
    _s("jenkins", "Jenkins", _CLOUD, ["jenkins pipeline"], ["ci/cd", "devops"]),
    _s("github actions", "GitHub Actions", _CLOUD, ["github workflows", "gh actions"], ["ci/cd", "github"]),
    _s("gitlab ci", "GitLab CI", _CLOUD, ["gitlab pipelines"], ["ci/cd", "gitlab"]),
    _s("ci/cd", "CI/CD", _CLOUD, ["continuous integration", "continuous delivery", "continuous deployment", "cicd"], ["github actions", "jenkins", "devops"]),
    _s("devops", "DevOps", _CLOUD, ["dev ops", "platform engineering"], ["docker", "ci/cd", "linux"]),
    _s("linux", "Linux", _CLOUD, ["unix", "ubuntu", "debian", "centos", "red hat"], ["bash", "operating systems"]),
    _s("nginx", "Nginx", _CLOUD, ["nginx server"], ["linux", "http"]),
    _s("serverless", "Serverless", _CLOUD, ["serverless architecture", "faas"], ["aws", "lambda"]),
    _s("lambda", "AWS Lambda", _CLOUD, ["aws lambda", "lambda functions"], ["serverless", "aws"]),
    _s("cloudformation", "CloudFormation", _CLOUD, ["aws cloudformation"], ["aws", "terraform"]),
    _s("helm", "Helm", _CLOUD, ["helm charts"], ["kubernetes"]),
    _s("prometheus", "Prometheus", _CLOUD, ["prometheus monitoring"], ["observability", "grafana"]),
    _s("grafana", "Grafana", _CLOUD, ["grafana dashboards"], ["observability", "prometheus"]),
    _s("observability", "Observability", _CLOUD, ["monitoring", "logging", "tracing", "telemetry"], ["prometheus", "grafana"]),
    _s("site reliability engineering", "Site Reliability Engineering", _CLOUD, ["sre", "reliability engineering"], ["devops", "observability"]),
    # Data & ML
    _s("machine learning", "Machine Learning", _DATA, ["ml", "supervised learning", "unsupervised learning"], ["deep learning", "scikit-learn", "statistics"]),
    _s("deep learning", "Deep Learning", _DATA, ["neural networks", "neural network", "dl"], ["machine learning", "tensorflow", "pytorch"]),
    _s("nlp", "Natural Language Processing", _DATA, ["natural language processing", "text mining"], ["machine learning", "llm"]),
    _s("computer vision", "Computer Vision", _DATA, ["image recognition", "cv"], ["deep learning", "opencv"]),
    _s("opencv", "OpenCV", _DATA, ["open cv"], ["computer vision", "python"]),
    _s("data analysis", "Data Analysis", _DATA, ["data analytics", "exploratory data analysis", "eda"], ["pandas", "sql", "statistics"]),
    _s("data visualization", "Data Visualization", _DATA, ["visualization", "dashboards"], ["tableau", "power bi", "data storytelling"]),
    _s("pandas", "pandas", _DATA, ["python pandas"], ["numpy", "data analysis"]),
    _s("numpy", "NumPy", _DATA, ["numpy arrays"], ["pandas", "python"]),
    _s("scikit-learn", "scikit-learn", _DATA, ["sklearn", "scikit learn"], ["machine learning", "python"]),
    _s("tensorflow", "TensorFlow", _DATA, ["tensor flow", "keras"], ["deep learning", "pytorch"]),
    _s("pytorch", "PyTorch", _DATA, ["torch", "pytorch lightning"], ["deep learning", "tensorflow"]),
    _s("keras", "Keras", _DATA, ["keras api"], ["tensorflow", "deep learning"]),
    _s("xgboost", "XGBoost", _DATA, ["xg boost", "lightgbm", "catboost"], ["machine learning", "scikit-learn"]),
    _s("spark", "Apache Spark", _DATA, ["apache spark", "pyspark", "spark sql"], ["hadoop", "big data"]),
    _s("hadoop", "Hadoop", _DATA, ["hdfs", "mapreduce"], ["spark", "big data"]),
    _s("airflow", "Apache Airflow", _DATA, ["apache airflow", "airflow dags"], ["etl", "data pipelines"]),
    _s("dbt", "dbt", _DATA, ["data build tool"], ["etl", "sql"]),
    _s("etl", "ETL", _DATA, ["extract transform load", "elt", "data pipelines"], ["airflow", "sql"]),
    _s("big data", "Big Data", _DATA, ["large-scale data"], ["spark", "hadoop"]),
    _s("statistics", "Statistics", _DATA, ["statistical analysis", "statistical modeling", "probability"], ["data analysis", "a/b testing"]),
    _s("a/b testing", "A/B Testing", _DATA, ["ab testing", "experimentation", "hypothesis testing"], ["statistics", "data analysis"]),
    _s("feature engineering", "Feature Engineering", _DATA, ["feature selection"], ["machine learning", "data analysis"]),
    _s("mlops", "MLOps", _DATA, ["ml ops", "model deployment", "model monitoring"], ["machine learning", "devops"]),
    _s("llm", "Large Language Models", _DATA, ["large language model", "llms", "language models"], ["nlp", "generative ai", "prompt engineering"]),
    _s("generative ai", "Generative AI", _DATA, ["genai", "gen ai"], ["llm", "prompt engineering"]),
    _s("prompt engineering", "Prompt Engineering", _DATA, ["prompt design"], ["llm", "generative ai"]),
    _s("rag", "Retrieval-Augmented Generation", _DATA, ["retrieval augmented generation", "rag pipeline"], ["llm", "vector databases"]),
    _s("vector databases", "Vector Databases", _DATA, ["vector database", "pinecone", "weaviate", "chromadb", "faiss"], ["rag", "embeddings"]),
    _s("embeddings", "Embeddings", _DATA, ["vector embeddings", "sentence embeddings"], ["nlp", "vector databases"]),
    _s("hugging face", "Hugging Face", _DATA, ["huggingface", "transformers library"], ["nlp", "llm"]),
    _s("openai api", "OpenAI API", _DATA, ["openai", "gpt api", "chatgpt api"], ["llm", "api design"]),
    _s("tableau", "Tableau", _DATA, ["tableau desktop"], ["data visualization", "power bi"]),
    _s("power bi", "Power BI", _DATA, ["powerbi", "microsoft power bi"], ["data visualization", "tableau"]),
    _s("excel", "Excel", _DATA, ["microsoft excel", "spreadsheets", "google sheets"], ["data analysis", "data visualization"]),
    _s("data storytelling", "Data Storytelling", _DATA, ["data presentation"], ["data visualization", "communication"]),
    # Testing & security
    _s("unit testing", "Unit Testing", _TESTING, ["unit tests", "unit test"], ["pytest", "jest", "tdd"]),
    _s("integration testing", "Integration Testing", _TESTING, ["integration tests", "end-to-end testing", "e2e testing"], ["test automation", "unit testing"]),
    _s("pytest", "pytest", _TESTING, ["py.test"], ["python", "unit testing"]),
    _s("jest", "Jest", _TESTING, ["jest testing"], ["javascript", "unit testing"]),
    _s("cypress", "Cypress", _TESTING, ["cypress.io"], ["test automation", "integration testing"]),
    _s("playwright", "Playwright", _TESTING, ["playwright testing"], ["test automation", "integration testing"]),
    _s("selenium", "Selenium", _TESTING, ["selenium webdriver"], ["test automation", "integration testing"]),
    _s("test automation", "Test Automation", _TESTING, ["automated testing", "automation testing"], ["pytest", "cypress", "selenium"]),
    _s("tdd", "Test-Driven Development", _TESTING, ["test driven development", "test-first development"], ["unit testing", "code review"]),
    _s("security", "Security", _TESTING, ["application security", "cybersecurity", "information security"], ["owasp", "secure coding", "authentication"]),
    _s("owasp", "OWASP", _TESTING, ["owasp top 10"], ["security", "secure coding"]),
    _s("penetration testing", "Penetration Testing", _TESTING, ["pen testing", "ethical hacking"], ["security", "owasp"]),
    _s("cryptography", "Cryptography", _TESTING, ["encryption", "hashing"], ["security", "secure coding"]),
    _s("secure coding", "Secure Coding", _TESTING, ["secure development", "security best practices"], ["security", "owasp"]),
    _s("code review", "Code Review", _TESTING, ["peer review", "pull request review"], ["git", "tdd"]),
    # Tools & practices
    _s("git", "Git", _TOOLS, ["version control", "git version control"], ["github", "gitlab"]),
    _s("github", "GitHub", _TOOLS, ["github.com", "github repositories"], ["git", "github actions"]),
    _s("gitlab", "GitLab", _TOOLS, ["gitlab.com"], ["git", "gitlab ci"]),
    _s("jira", "Jira", _TOOLS, ["atlassian jira"], ["agile", "confluence"]),
    _s("confluence", "Confluence", _TOOLS, ["atlassian confluence"], ["jira", "documentation"]),
    _s("postman", "Postman", _TOOLS, ["postman collections"], ["rest apis", "api design"]),
    _s("vs code", "VS Code", _TOOLS, ["visual studio code", "vscode"], ["git", "debugging"]),
    _s("vim", "Vim", _TOOLS, ["neovim", "vi editor"], ["linux"]),
    _s("agile", "Agile", _TOOLS, ["agile methodology", "agile development"], ["scrum", "kanban"]),
    _s("scrum", "Scrum", _TOOLS, ["scrum master", "sprint planning"], ["agile", "kanban"]),
    _s("kanban", "Kanban", _TOOLS, ["kanban board"], ["agile", "scrum"]),
    _s("project management", "Project Management", _TOOLS, ["program management", "project planning"], ["agile", "stakeholder management"]),
    _s("technical writing", "Technical Writing", _TOOLS, ["technical documentation", "documentation"], ["communication", "confluence"]),
    _s("debugging", "Debugging", _TOOLS, ["troubleshooting", "root cause analysis"], ["testing", "problem solving"]),
    _s("performance optimization", "Performance Optimization", _TOOLS, ["performance tuning", "optimization", "profiling"], ["caching", "debugging"]),
    _s("system design", "System Design", _TOOLS, ["systems design", "software architecture", "architecture design"], ["distributed systems", "microservices"]),
    _s("distributed systems", "Distributed Systems", _TOOLS, ["distributed computing", "distributed architecture"], ["system design", "microservices"]),
    _s("scalability", "Scalability", _TOOLS, ["scalable systems", "high availability"], ["system design", "performance optimization"]),
    # CS fundamentals
    _s("data structures", "Data Structures", _CS, ["data structure"], ["algorithms", "computer science fundamentals"]),
    _s("algorithms", "Algorithms", _CS, ["algorithm design", "algorithm"], ["data structures", "problem solving"]),
    _s("object-oriented programming", "Object-Oriented Programming", _CS, ["oop", "object oriented design", "solid principles"], ["design patterns", "java"]),
    _s("design patterns", "Design Patterns", _CS, ["software design patterns", "gang of four"], ["object-oriented programming", "system design"]),
    _s("operating systems", "Operating Systems", _CS, ["os concepts", "process management", "memory management"], ["linux", "computer networks"]),
    _s("computer networks", "Computer Networks", _CS, ["networking", "tcp/ip", "network protocols"], ["http", "operating systems"]),
    _s("dbms", "Database Management Systems", _CS, ["database management system", "dbms concepts"], ["sql", "database design"]),
    _s("computer science fundamentals", "Computer Science Fundamentals", _CS, ["cs fundamentals", "fundamentals of computer science"], ["data structures", "algorithms"]),
    # Soft skills
    _s("communication", "Communication", _SOFT, ["verbal communication", "written communication", "communicating"], ["presentation", "stakeholder management"]),
    _s("leadership", "Leadership", _SOFT, ["team leadership", "leading teams", "people management"], ["mentoring", "communication"]),
    _s("teamwork", "Teamwork", _SOFT, ["team player", "collaboration", "collaborative"], ["communication", "conflict resolution"]),
    _s("problem solving", "Problem Solving", _SOFT, ["analytical thinking", "troubleshooting"], ["critical thinking", "debugging"]),
    _s("critical thinking", "Critical Thinking", _SOFT, ["analytical skills", "analysis skills"], ["problem solving"]),
    _s("mentoring", "Mentoring", _SOFT, ["coaching", "mentorship"], ["leadership", "communication"]),
    _s("stakeholder management", "Stakeholder Management", _SOFT, ["stakeholder communication", "stakeholder engagement"], ["communication", "project management"]),
    _s("presentation", "Presentation", _SOFT, ["public speaking", "presenting"], ["communication", "data storytelling"]),
    _s("time management", "Time Management", _SOFT, ["prioritization", "prioritisation"], ["project management"]),
    _s("adaptability", "Adaptability", _SOFT, ["flexibility", "fast learner", "quick learner"], ["problem solving"]),
    _s("attention to detail", "Attention to Detail", _SOFT, ["detail-oriented", "detail oriented"], ["code review", "testing"]),
    _s("conflict resolution", "Conflict Resolution", _SOFT, ["conflict management"], ["communication", "teamwork"]),
    _s("customer focus", "Customer Focus", _SOFT, ["customer-centric", "customer obsession"], ["communication", "product management"]),
    _s("negotiation", "Negotiation", _SOFT, ["negotiating"], ["communication", "stakeholder management"]),
    # Business & product
    _s("product management", "Product Management", _BUSINESS, ["product owner", "product strategy"], ["agile", "market research"]),
    _s("market research", "Market Research", _BUSINESS, ["competitive analysis", "user research"], ["product management", "data analysis"]),
    _s("business analysis", "Business Analysis", _BUSINESS, ["business analyst", "requirements analysis"], ["requirements gathering", "communication"]),
    _s("requirements gathering", "Requirements Gathering", _BUSINESS, ["requirements elicitation", "user stories"], ["business analysis", "agile"]),
    _s("okrs", "OKRs", _BUSINESS, ["objectives and key results"], ["project management", "product management"]),
    _s("analytics", "Analytics", _BUSINESS, ["product analytics", "web analytics", "google analytics"], ["data analysis", "a/b testing"]),
    _s("seo", "SEO", _BUSINESS, ["search engine optimization"], ["content marketing", "analytics"]),
    _s("content marketing", "Content Marketing", _BUSINESS, ["content strategy"], ["seo", "communication"]),
    _s("salesforce", "Salesforce", _BUSINESS, ["salesforce crm"], ["crm", "business analysis"]),
    _s("sap", "SAP", _BUSINESS, ["sap erp"], ["business analysis", "erp"]),
    _s("workday", "Workday", _BUSINESS, ["workday hcm"], ["business analysis", "hr systems"]),
    _s("crm", "CRM", _BUSINESS, ["customer relationship management"], ["salesforce", "business analysis"]),
    _s("erp", "ERP", _BUSINESS, ["enterprise resource planning"], ["sap", "business analysis"]),
)

SKILL_BY_NAME: dict[str, Skill] = {skill.name: skill for skill in SKILL_TAXONOMY}

# Backwards-compatible mapping used by older modules and callers.
SKILLS: dict[str, list[str]] = {skill.name: list(skill.aliases) for skill in SKILL_TAXONOMY}

DISPLAY_NAMES: dict[str, str] = {skill.name: skill.display for skill in SKILL_TAXONOMY}

CATEGORIES: dict[str, list[str]] = {}
for _skill in SKILL_TAXONOMY:
    CATEGORIES.setdefault(_skill.category, []).append(_skill.name)


def _alias_pattern(alias: str, case_sensitive: bool = False) -> re.Pattern[str]:
    alias = alias.strip()
    escaped = re.escape(alias)
    flags = 0 if case_sensitive else re.IGNORECASE
    # Word-ish boundaries: do not match inside alphanumeric identifiers.
    # Short aliases (``js``, ``ts``, ``go``, ``r``) must also not match the
    # tail of a dotted product name such as ``React.js``.
    prefix = r"(?<![A-Za-z0-9.])" if len(alias) <= 3 else r"(?<![A-Za-z0-9])"
    return re.compile(prefix + escaped + r"(?![A-Za-z0-9])", flags)


_ALIAS_INDEX: list[tuple[Skill, str, re.Pattern[str]]] = []
for _skill in SKILL_TAXONOMY:
    for _alias in _skill.aliases:
        case_sensitive = _alias in _skill.case_sensitive_aliases
        _ALIAS_INDEX.append((_skill, _alias, _alias_pattern(_alias, case_sensitive)))


def find_occurrences(text: str) -> list[dict]:
    """Return all alias occurrences, longest alias first to avoid double labels."""
    found: list[dict] = []
    for skill, alias, pattern in _ALIAS_INDEX:
        for match in pattern.finditer(text):
            found.append(
                {
                    "skill": skill.name,
                    "alias": alias,
                    "start": match.start(),
                    "end": match.end(),
                    "surface": match.group(0),
                }
            )
    # If two aliases of the same skill overlap, keep the longest surface form.
    found.sort(key=lambda item: (item["start"], -(item["end"] - item["start"])))
    deduped: list[dict] = []
    for item in found:
        if deduped and item["skill"] == deduped[-1]["skill"] and item["start"] < deduped[-1]["end"]:
            if item["end"] - item["start"] > deduped[-1]["end"] - deduped[-1]["start"]:
                deduped[-1] = item
            continue
        deduped.append(item)
    return deduped


def extract_canonical_skills(text: str) -> list[str]:
    """Return canonical skill identifiers in taxonomy order.

    Matching is alias- and word-boundary based. There is deliberately no
    substring fallback: it would make ``java`` match ``javascript``.
    """
    present = {item["skill"] for item in find_occurrences(text)}
    return [skill.name for skill in SKILL_TAXONOMY if skill.name in present]


def display_name(skill: str) -> str:
    return DISPLAY_NAMES.get(skill, skill.title())


def category_of(skill: str) -> str:
    entry = SKILL_BY_NAME.get(skill)
    return entry.category if entry else "Other"


def related_skills(skill: str) -> tuple[str, ...]:
    entry = SKILL_BY_NAME.get(skill)
    return entry.related if entry else ()


def implied_skills(skill: str) -> tuple[str, ...]:
    entry = SKILL_BY_NAME.get(skill)
    return entry.implies if entry else ()
