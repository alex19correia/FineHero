# Master Research Execution Prompt

## 🎯 **OBJECTIVE**
Execute a comprehensive sequential research campaign using multiple advanced web scraping and content discovery tools to build a complete knowledge base on the specified research topic.

## 🔧 **AVAILABLE RESEARCH TOOLS**

You have access to the following research execution framework in the workspace:

### **Core Research Scripts (Execute in Order):**

1. **`run_crawl4ai_finehero_simple.py`** - Basic Crawl4AI implementation
   - Purpose: Entry-level web crawling with error handling
   - Run with: `python run_crawl4ai_finehero_simple.py`

2. **`scripts/research_and_grow_knowledge_base.py`** - Active Research System
   - Purpose: Proactive content discovery and knowledge base integration
   - Run with: `python scripts/research_and_grow_knowledge_base.py`

3. **`scripts/modern_content_discovery.py`** - Advanced Modern Framework
   - Purpose: AI-optimized content extraction using Crawl4AI + Firecrawl
   - Run with: `python scripts/modern_content_discovery.py`

### **Universal Research Tools:**

4. **`backend/services/web_scraper.py`** - Universal Scraper Class
   - Purpose: Configurable multi-source web scraping
   - Usage: `python cli/main.py scrape [source] --start-url [url] --max-pages 10`

5. **`portuguese_appeal_templates_scraper.py`** - Template Research System
   - Purpose: Find and analyze content templates from multiple sources
   - Run with: Direct execution

## 📋 **EXECUTION PROTOCOL**

### **Phase 1: Basic Research Foundation**
```
Execute: python run_crawl4ai_finehero_simple.py
Expected Output: Initial crawl results, success rate analysis
Success Criteria: At least 1 successful crawl from target sources
```

### **Phase 2: Active Content Discovery**
```
Execute: python scripts/research_and_grow_knowledge_base.py
Expected Output: New content found and integrated
Success Criteria: New legal documents, court decisions, fine examples discovered
```

### **Phase 3: Advanced Content Extraction**
```
Execute: python scripts/modern_content_discovery.py
Expected Output: AI-enhanced content discovery results
Success Criteria: High-quality content extraction with quality scoring
```

### **Phase 4: Universal Web Scraping**
```
Execute: python cli/main.py scrape [customize source] --start-url [url] --max-pages 10
Expected Output: Custom source scraping results
Success Criteria: Successful document discovery and downloading
```

### **Phase 5: Template and Pattern Research**
```
Execute: python portuguese_appeal_templates_scraper.py
Expected Output: Template discovery and analysis
Success Criteria: Templates found and categorized by quality
```

## 📊 **REASSESSMENT CRITERIA**

After executing each script, perform comprehensive analysis:

### **Quantitative Metrics:**
- **Success Rate**: % of successful crawls vs attempted
- **Content Volume**: Total characters/pages extracted
- **Quality Scores**: Average content quality rating (0-1 scale)
- **Processing Speed**: Time per successful extraction
- **Error Rate**: % of failed operations

### **Qualitative Assessment:**
- **Content Relevance**: How well content matches research objectives
- **Source Authority**: Credibility of discovered sources
- **Completeness**: Coverage of research topic areas
- **Timeliness**: Recency of discovered content
- **Usability**: How well content can be integrated into knowledge base

### **Output Analysis:**
- **File Generation**: Check created output files and directories
- **Data Structure**: Validate JSON/markdown formatting
- **Knowledge Base Integration**: Confirm successful integration results
- **Error Logs**: Review and categorize any failures

## 🔄 **ADAPTIVE EXECUTION**

If any script fails or underperforms:

1. **Error Analysis**: Examine failure reasons (network, authentication, parsing)
2. **Retry Logic**: Re-run failed components with modified parameters
3. **Alternative Sources**: Use different target URLs or search terms
4. **Manual Intervention**: Identify points requiring human oversight

## 📈 **PROGRESS TRACKING**

Create a real-time execution dashboard tracking:

```
Phase 1: Basic Research
├── Crawl4AI Test Results: [SUCCESS/FAILED]
├── Target Sources Crawled: [X/Y]
├── Content Extracted: [X characters]
└── Phase Status: [COMPLETE/RETRY/FAILED]

Phase 2: Active Discovery
├── DRE Content Search: [X new docs found]
├── Court Decisions: [X new decisions]
├── Fine Examples: [X new examples]
└── Integration Status: [SUCCESS/FAILED]

Phase 3: Advanced Extraction
├── AI-Enhanced Crawls: [X successful]
├── Content Quality Scores: [Average X.X]
├── Knowledge Base Updates: [X entries added]
└── Phase Status: [COMPLETE/RETRY/FAILED]

[Continue for all phases...]
```

## 📝 **FINAL REASSESSMENT REPORT**

Generate comprehensive report including:

### **Executive Summary**
- Total research campaign duration
- Overall success rate
- Content volume summary
- Key discoveries

### **Performance Analysis**
- Individual script performance
- Comparative efficiency metrics
- Cost-benefit analysis (time vs results)
- Scalability assessment

### **Knowledge Base Impact**
- New entries added
- Quality improvements
- Gap analysis (what's still missing)
- Integration success rate

### **Recommendations**
- Optimal script combinations for different research types
- Performance optimization opportunities
- Automation enhancement suggestions
- Scaling strategy for production use

## 🚨 **CRITICAL REQUIREMENTS**

1. **Sequential Execution**: Complete Phase 1 before Phase 2, etc.
2. **Error Handling**: Document all failures and provide fallback strategies
3. **Result Validation**: Verify all outputs before proceeding
4. **Resource Monitoring**: Track computational and network usage
5. **Progress Reporting**: Update execution status after each phase

## 🎯 **EXPECTED OUTCOMES**

Upon successful completion, you should have:
- Comprehensive content discovery from multiple sources
- Structured knowledge base with quality-scored entries
- Detailed performance analysis and recommendations
- Proven framework for reproducible research campaigns
- Clear understanding of tool capabilities and limitations

---

## 🔧 **READY TO EXECUTE**

You now have a complete research execution framework. The prompt is designed for LLM systems with tool access to execute these commands and provide comprehensive analysis of the results.

**Begin execution with Phase 1 and proceed sequentially through all phases, reassessing after each step.**