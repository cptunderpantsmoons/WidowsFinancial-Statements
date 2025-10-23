import statistics
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from utils.logger import Logger
from .knowledge_extractor import KnowledgeExtractor
from .financial_validator import AnalysisResult

logger = Logger(__name__)

@dataclass
class BenchmarkComparison:
    """Benchmark comparison result."""
    metric_name: str
    company_value: float
    benchmark_mean: float
    benchmark_percentile: float
    variance_percent: float
    performance_level: str  # 'Excellent', 'Good', 'Average', 'Below Average', 'Poor'
    industry_context: str

@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    metric_name: str
    current_value: float
    historical_values: List[float]
    trend_direction: str  # 'Improving', 'Declining', 'Stable'
    trend_percent: float
    volatility: float
    forecast_next: Optional[float]

@dataclass
class Insight:
    """Financial insight or recommendation."""
    category: str  # 'Performance', 'Risk', 'Opportunity', 'Compliance'
    priority: str  # 'High', 'Medium', 'Low'
    title: str
    description: str
    quantitative_evidence: Optional[str]
    recommendation: Optional[str]

class FinancialAnalyzer:
    """Comprehensive financial analysis and benchmarking."""
    
    def __init__(self):
        self.knowledge_base = KnowledgeExtractor()
        self.industry_benchmarks = self._initialize_industry_benchmarks()
        self.analysis_thresholds = self._initialize_analysis_thresholds()
    
    def _initialize_industry_benchmarks(self) -> Dict:
        """Initialize industry benchmark data."""
        # This would typically come from external data sources
        # Using representative values for key industries
        return {
            'technology': {
                'current_ratio': {'mean': 2.1, 'median': 1.8, 'p75': 2.5, 'p25': 1.4},
                'debt_to_equity': {'mean': 0.4, 'median': 0.3, 'p75': 0.6, 'p25': 0.2},
                'gross_profit_margin': {'mean': 45.0, 'median': 42.0, 'p75': 55.0, 'p25': 35.0},
                'net_profit_margin': {'mean': 12.0, 'median': 10.0, 'p75': 18.0, 'p25': 5.0},
                'return_on_assets': {'mean': 10.0, 'median': 8.0, 'p75': 15.0, 'p25': 3.0},
                'return_on_equity': {'mean': 18.0, 'median': 15.0, 'p75': 25.0, 'p25': 8.0}
            },
            'manufacturing': {
                'current_ratio': {'mean': 1.8, 'median': 1.6, 'p75': 2.2, 'p25': 1.3},
                'debt_to_equity': {'mean': 0.7, 'median': 0.6, 'p75': 1.0, 'p25': 0.4},
                'gross_profit_margin': {'mean': 28.0, 'median': 25.0, 'p75': 35.0, 'p25': 20.0},
                'net_profit_margin': {'mean': 6.0, 'median': 5.0, 'p75': 10.0, 'p25': 2.0},
                'return_on_assets': {'mean': 6.0, 'median': 5.0, 'p75': 10.0, 'p25': 2.0},
                'return_on_equity': {'mean': 12.0, 'median': 10.0, 'p75': 18.0, 'p25': 5.0}
            },
            'retail': {
                'current_ratio': {'mean': 1.5, 'median': 1.4, 'p75': 1.8, 'p25': 1.1},
                'debt_to_equity': {'mean': 0.8, 'median': 0.7, 'p75': 1.2, 'p25': 0.4},
                'gross_profit_margin': {'mean': 32.0, 'median': 30.0, 'p75': 40.0, 'p25': 25.0},
                'net_profit_margin': {'mean': 3.5, 'median': 3.0, 'p75': 6.0, 'p25': 1.0},
                'return_on_assets': {'mean': 4.0, 'median': 3.5, 'p75': 7.0, 'p25': 1.5},
                'return_on_equity': {'mean': 8.0, 'median': 7.0, 'p75': 12.0, 'p25': 3.0}
            }
        }
    
    def _initialize_analysis_thresholds(self) -> Dict:
        """Initialize thresholds for determining performance levels."""
        return {
            'excellent': 0.75,  # Top 25%
            'good': 0.50,      # Top 25-50%
            'average': 0.25,   # Top 25-75%
            'below_average': 0.10,  # Bottom 10-25%
            'poor': 0.10       # Bottom 10%
        }
    
    def perform_comprehensive_analysis(
        self, 
        data: Dict[str, float], 
        industry: str = 'technology',
        historical_data: Optional[Dict[str, List[float]]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive financial analysis."""
        logger.info(f"Starting comprehensive analysis for {industry} industry")
        
        analysis_results = {
            'financial_ratios': {},
            'benchmark_comparisons': [],
            'trend_analysis': [],
            'insights': [],
            'risk_assessment': {},
            'performance_grade': {}
        }
        
        try:
            # Calculate financial ratios
            from .financial_validator import FinancialValidator
            validator = FinancialValidator()
            ratios = validator._calculate_financial_ratios(data)
            analysis_results['financial_ratios'] = ratios
            
            # Benchmark comparisons
            for ratio_name, ratio_value in ratios.items():
                if ratio_value is not None and ratio_name in self.industry_benchmarks[industry]:
                    benchmark_comp = self._compare_to_benchmark(
                        ratio_name, ratio_value, industry
                    )
                    analysis_results['benchmark_comparisons'].append(benchmark_comp)
            
            # Trend analysis if historical data available
            if historical_data:
                for metric_name, hist_values in historical_data.items():
                    if len(hist_values) >= 2:
                        current_value = data.get(metric_name)
                        if current_value is not None:
                            trend = self._analyze_trend(
                                metric_name, current_value, hist_values
                            )
                            analysis_results['trend_analysis'].append(trend)
            
            # Generate insights
            insights = self._generate_insights(
                ratios, analysis_results['benchmark_comparisons'], 
                analysis_results['trend_analysis']
            )
            analysis_results['insights'] = insights
            
            # Risk assessment
            risk_assessment = self._assess_financial_risk(data, ratios)
            analysis_results['risk_assessment'] = risk_assessment
            
            # Overall performance grade
            performance_grade = self._calculate_performance_grade(
                analysis_results['benchmark_comparisons']
            )
            analysis_results['performance_grade'] = performance_grade
            
            logger.info("Comprehensive analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return analysis_results
    
    def _compare_to_benchmark(
        self, 
        ratio_name: str, 
        company_value: float, 
        industry: str
    ) -> BenchmarkComparison:
        """Compare company metric to industry benchmarks."""
        industry_data = self.industry_benchmarks[industry].get(ratio_name, {})
        if not industry_data:
            return BenchmarkComparison(
                metric_name=ratio_name,
                company_value=company_value,
                benchmark_mean=0,
                benchmark_percentile=0,
                variance_percent=0,
                performance_level='Average',
                industry_context='No benchmark data available'
            )
        
        mean_value = industry_data['mean']
        median_value = industry_data['median']
        p25 = industry_data['p25']
        p75 = industry_data['p75']
        
        # Calculate percentile
        percentile = self._estimate_percentile(company_value, p25, median_value, p75)
        
        # Calculate variance from mean
        variance_percent = ((company_value - mean_value) / mean_value) * 100 if mean_value != 0 else 0
        
        # Determine performance level
        if percentile >= 75:
            performance_level = 'Excellent'
        elif percentile >= 50:
            performance_level = 'Good'
        elif percentile >= 25:
            performance_level = 'Average'
        elif percentile >= 10:
            performance_level = 'Below Average'
        else:
            performance_level = 'Poor'
        
        # Generate industry context
        context = self._generate_industry_context(ratio_name, company_value, percentile, industry)
        
        return BenchmarkComparison(
            metric_name=ratio_name,
            company_value=company_value,
            benchmark_mean=mean_value,
            benchmark_percentile=percentile,
            variance_percent=variance_percent,
            performance_level=performance_level,
            industry_context=context
        )
    
    def _estimate_percentile(self, value: float, p25: float, median: float, p75: float) -> float:
        """Estimate percentile based on value relative to quartiles."""
        if value <= p25:
            # Linear interpolation from 0 to 25th percentile
            if p25 == 0:
                return 0
            return max(0, min(25, (value / p25) * 25))
        elif value <= median:
            # Linear interpolation from 25th to 50th percentile
            if median - p25 == 0:
                return 25
            return 25 + max(0, min(25, ((value - p25) / (median - p25)) * 25))
        elif value <= p75:
            # Linear interpolation from 50th to 75th percentile
            if p75 - median == 0:
                return 50
            return 50 + max(0, min(25, ((value - median) / (p75 - median)) * 25))
        else:
            # Linear interpolation from 75th to 100th percentile
            if p75 == 0:
                return 75
            return 75 + max(0, min(25, ((value - p75) / p75) * 25))
    
    def _generate_industry_context(self, ratio_name: str, value: float, percentile: float, industry: str) -> str:
        """Generate industry-specific context for the metric."""
        contexts = {
            'current_ratio': {
                'technology': f"The current ratio of {value:.2f} is {'above' if percentile > 50 else 'below'} the tech industry median. Tech companies typically maintain higher liquidity ratios due to rapid growth needs.",
                'manufacturing': f"The current ratio of {value:.2f} reflects {'strong' if percentile > 50 else 'moderate'} working capital management typical in manufacturing.",
                'retail': f"The current ratio of {value:.2f} indicates {'efficient' if percentile > 50 else 'constrained'} cash management in the retail sector."
            },
            'debt_to_equity': {
                'technology': f"The debt-to-equity ratio of {value:.2f} shows {'conservative' if percentile < 50 else 'aggressive'} financing, with tech companies often using less debt.",
                'manufacturing': f"The debt-to-equity ratio of {value:.2f} reflects the capital-intensive nature of manufacturing.",
                'retail': f"The debt-to-equity ratio of {value:.2f} is {'typical' if 30 <= percentile <= 70 else 'unusual'} for retail operations."
            },
            'gross_profit_margin': {
                'technology': f"The gross margin of {value:.1f}% is {'competitive' if percentile > 50 else 'below industry norms'} for technology products/services.",
                'manufacturing': f"The gross margin of {value:.1f}% reflects {'efficient' if percentile > 50 else 'cost-pressured'} manufacturing operations.",
                'retail': f"The gross margin of {value:.1f}% is {'healthy' if percentile > 50 else 'tight'} for retail margins."
            }
        }
        
        return contexts.get(ratio_name, {}).get(industry, f"The {ratio_name} of {value:.2f} shows performance in the {percentile:.0f}th percentile for {industry} companies.")
    
    def _analyze_trend(self, metric_name: str, current_value: float, historical_values: List[float]) -> TrendAnalysis:
        """Analyze trend of a metric over time."""
        if len(historical_values) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                current_value=current_value,
                historical_values=historical_values,
                trend_direction='Unknown',
                trend_percent=0,
                volatility=0,
                forecast_next=None
            )
        
        # Calculate trend using linear regression (simplified)
        n = len(historical_values)
        x_values = list(range(n))
        y_values = historical_values
        
        # Simple linear regression
        mean_x = sum(x_values) / n
        mean_y = sum(y_values) / n
        
        numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
        denominator = sum((x_values[i] - mean_x) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Determine trend direction
        if abs(slope) < 0.01:
            trend_direction = 'Stable'
        elif slope > 0:
            trend_direction = 'Improving'
        else:
            trend_direction = 'Declining'
        
        # Calculate trend percent change
        if historical_values[0] != 0:
            trend_percent = ((current_value - historical_values[0]) / historical_values[0]) * 100
        else:
            trend_percent = 0
        
        # Calculate volatility (standard deviation)
        if n > 1:
            variance = sum((val - mean_y) ** 2 for val in y_values) / n
            volatility = (variance ** 0.5) / mean_y if mean_y != 0 else 0
        else:
            volatility = 0
        
        # Simple forecast (next period)
        if len(historical_values) >= 3:
            # Simple linear extrapolation
            forecast = historical_values[-1] + slope
            forecast_next = max(0, forecast)  # Ensure non-negative for financial metrics
        else:
            forecast_next = None
        
        return TrendAnalysis(
            metric_name=metric_name,
            current_value=current_value,
            historical_values=historical_values,
            trend_direction=trend_direction,
            trend_percent=trend_percent,
            volatility=volatility,
            forecast_next=forecast_next
        )
    
    def _generate_insights(
        self, 
        ratios: Dict[str, float], 
        benchmarks: List[BenchmarkComparison],
        trends: List[TrendAnalysis]
    ) -> List[Insight]:
        """Generate actionable insights from analysis."""
        insights = []
        
        # Analyze benchmark performance
        excellent_metrics = [b for b in benchmarks if b.performance_level == 'Excellent']
        poor_metrics = [b for b in benchmarks if b.performance_level in ['Poor', 'Below Average']]
        
        if excellent_metrics:
            insights.append(Insight(
                category='Performance',
                priority='High',
                title='Outstanding Performance Areas',
                description=f"The company excels in {len(excellent_metrics)} key metrics compared to industry peers.",
                quantitative_evidence=f"Excelling in: {', '.join(m.metric_name.replace('_', ' ').title() for m in excellent_metrics)}",
                recommendation="Leverage these strengths in investor communications and competitive positioning."
            ))
        
        if poor_metrics:
            insights.append(Insight(
                category='Risk',
                priority='High',
                title='Areas Requiring Attention',
                description=f"The company underperforms industry benchmarks in {len(poor_metrics)} critical areas.",
                quantitative_evidence=f"Needs improvement in: {', '.join(m.metric_name.replace('_', ' ').title() for m in poor_metrics)}",
                recommendation="Develop specific action plans to address these performance gaps."
            ))
        
        # Analyze trends
        declining_trends = [t for t in trends if t.trend_direction == 'Declining' and abs(t.trend_percent) > 10]
        if declining_trends:
            insights.append(Insight(
                category='Risk',
                priority='Medium',
                title='Negative Trends Detected',
                description=f"Significant negative trends observed in {len(declining_trends)} metrics.",
                quantitative_evidence=f"Declining metrics: {', '.join(t.metric_name for t in declining_trends)}",
                recommendation="Investigate root causes of declining performance and implement corrective measures."
            ))
        
        # Financial health assessment
        if ratios:
            # Check for liquidity issues
            current_ratio = ratios.get('current_ratio')
            if current_ratio and current_ratio < 1.0:
                insights.append(Insight(
                    category='Risk',
                    priority='High',
                    title='Liquidity Concern',
                    description=f"Current ratio of {current_ratio:.2f} below recommended minimum of 1.0.",
                    quantitative_evidence=f"Current ratio: {current_ratio:.2f} (industry median: ~1.8)",
                    recommendation="Improve cash management or reduce current liabilities to enhance liquidity."
                ))
            
            # Check for excessive leverage
            debt_to_equity = ratios.get('debt_to_equity')
            if debt_to_equity and debt_to_equity > 1.5:
                insights.append(Insight(
                    category='Risk',
                    priority='High',
                    title='High Financial Leverage',
                    description=f"Debt-to-equity ratio of {debt_to_equity:.2f} indicates elevated financial risk.",
                    quantitative_evidence=f"Debt-to-equity: {debt_to_equity:.2f} (industry median: ~0.6)",
                    recommendation="Consider debt restructuring or equity infusion to reduce financial risk."
                ))
            
            # Check profitability
            net_margin = ratios.get('net_profit_margin')
            if net_margin and net_margin < 2:
                insights.append(Insight(
                    category='Performance',
                    priority='Medium',
                    title='Low Profitability',
                    description=f"Net profit margin of {net_margin:.1f}% suggests operational efficiency challenges.",
                    quantitative_evidence=f"Net profit margin: {net_margin:.1f}% (industry median: ~10%)",
                    recommendation="Review cost structure and pricing strategies to improve profitability."
                ))
            
            elif net_margin and net_margin > 20:
                insights.append(Insight(
                    category='Opportunity',
                    priority='Medium',
                    title='Exceptional Profitability',
                    description=f"Net profit margin of {net_margin:.1f}% indicates strong competitive advantages.",
                    quantitative_evidence=f"Net profit margin: {net_margin:.1f}% (exceeding industry norms)",
                    recommendation="Leverage competitive advantages and explore growth opportunities while maintaining margin discipline."
                ))
        
        return insights
    
    def _assess_financial_risk(self, data: Dict[str, float], ratios: Dict[str, float]) -> Dict:
        """Assess comprehensive financial risk."""
        risk_factors = []
        overall_risk_score = 0
        
        # Liquidity risk
        current_ratio = ratios.get('current_ratio')
        if current_ratio:
            if current_ratio < 1.0:
                risk_factors.append({'type': 'Liquidity', 'severity': 'High', 'score': 75, 'description': f'Current ratio insufficient at {current_ratio:.2f}'})
            elif current_ratio < 1.5:
                risk_factors.append({'type': 'Liquidity', 'severity': 'Medium', 'score': 50, 'description': f'Current ratio below optimal at {current_ratio:.2f}'})
            else:
                risk_factors.append({'type': 'Liquidity', 'severity': 'Low', 'score': 25, 'description': f'Current ratio healthy at {current_ratio:.2f}'})
        
        # Solvency risk
        debt_to_equity = ratios.get('debt_to_equity')
        if debt_to_equity:
            if debt_to_equity > 1.5:
                risk_factors.append({'type': 'Solvency', 'severity': 'High', 'score': 80, 'description': f'High leverage at {debt_to_equity:.2f}'})
            elif debt_to_equity > 1.0:
                risk_factors.append({'type': 'Solvency', 'severity': 'Medium', 'score': 60, 'description': f'Elevated leverage at {debt_to_equity:.2f}'})
            else:
                risk_factors.append({'type': 'Solvency', 'severity': 'Low', 'score': 20, 'description': f'Moderate leverage at {debt_to_equity:.2f}'})
        
        # Profitability risk
        net_margin = ratios.get('net_profit_margin')
        if net_margin is not None:
            if net_margin < 0:
                risk_factors.append({'type': 'Profitability', 'severity': 'Critical', 'score': 100, 'description': f'Negative profit margin of {net_margin:.1f}%'})
            elif net_margin < 2:
                risk_factors.append({'type': 'Profitability', 'severity': 'High', 'score': 70, 'description': f'Very low profit margin of {net_margin:.1f}%'})
            elif net_margin < 5:
                risk_factors.append({'type': 'Profitability', 'severity': 'Medium', 'score': 45, 'description': f'Low profit margin of {net_margin:.1f}%'})
            else:
                risk_factors.append({'type': 'Profitability', 'severity': 'Low', 'score': 15, 'description': f'Healthy profit margin of {net_margin:.1f}%'})
        
        # Calculate overall risk score (weighted average)
        if risk_factors:
            total_score = sum(rf['score'] for rf in risk_factors)
            overall_risk_score = total_score / len(risk_factors)
        
        # Determine risk level
        if overall_risk_score >= 75:
            risk_level = 'Critical'
        elif overall_risk_score >= 60:
            risk_level = 'High'
        elif overall_risk_score >= 40:
            risk_level = 'Medium'
        elif overall_risk_score >= 25:
            risk_level = 'Low'
        else:
            risk_level = 'Very Low'
        
        return {
            'overall_risk_score': round(overall_risk_score, 1),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendation': self._get_risk_recommendation(risk_level, risk_factors)
        }
    
    def _get_risk_recommendation(self, risk_level: str, risk_factors: List[Dict]) -> str:
        """Get risk-level specific recommendations."""
        recommendations = {
            'Critical': "Immediate action required. Address all critical risk factors, consider emergency capital infusion, and seek professional financial advice.",
            'High': "Develop comprehensive risk mitigation plan within 30 days. Focus on highest severity factors first.",
            'Medium': "Monitor risk factors quarterly and implement preventive measures. Consider strategic improvements.",
            'Low': "Continue monitoring and maintain current financial policies. Focus on optimizing operations.",
            'Very Low': "Excellent financial health. Consider strategic growth opportunities while maintaining discipline."
        }
        
        return recommendations.get(risk_level, "Assess risk factors and develop appropriate response strategies.")
    
    def _calculate_performance_grade(self, benchmarks: List[BenchmarkComparison]) -> Dict:
        """Calculate overall performance grade."""
        if not benchmarks:
            return {'grade': 'N/A', 'score': 0, 'summary': 'No benchmarks available'}
        
        # Calculate weighted score
        total_score = 0
        weighting_factors = {
            'liquidity_ratios': 0.25,  # Current ratio, quick ratio
            'profitability_ratios': 0.35,  # Profit margins, returns
            'leverage_ratios': 0.20,  # Debt ratios
            'efficiency_ratios': 0.20   # Asset utilization
        }
        
        categorized_scores = {
            'liquidity_ratios': [],
            'profitability_ratios': [],
            'leverage_ratios': [],
            'efficiency_ratios': []
        }
        
        for benchmark in benchmarks:
            # Assign benchmark to category (simplified)
            if 'ratio' in benchmark.metric_name:
                if 'current' in benchmark.metric_name.lower() or 'quick' in benchmark.metric_name.lower():
                    categorized_scores['liquidity_ratios'].append(benchmark.benchmark_percentile)
                elif 'debt' in benchmark.metric_name.lower() or 'equity' in benchmark.metric_name.lower():
                    categorized_scores['leverage_ratios'].append(benchmark.benchmark_percentile)
                else:
                    categorized_scores['efficiency_ratios'].append(benchmark.benchmark_percentile)
            elif 'margin' in benchmark.metric_name.lower() or 'return' in benchmark.metric_name.lower():
                categorized_scores['profitability_ratios'].append(benchmark.benchmark_percentile)
        
        # Calculate weighted score
        final_score = 0
        category_count = 0
        
        for category, scores in categorized_scores.items():
            if scores:
                category_avg = sum(scores) / len(scores)
                final_score += category_avg * weighting_factors.get(category, 0.25)
                category_count += 1
        
        # Determine grade
        if final_score >= 85:
            grade = 'A+'
        elif final_score >= 75:
            grade = 'A'
        elif final_score >= 70:
            grade = 'A-'
        elif final_score >= 65:
            grade = 'B+'
        elif final_score >= 60:
            grade = 'B'
        elif final_score >= 55:
            grade = 'B-'
        elif final_score >= 50:
            grade = 'C+'
        elif final_score >= 45:
            grade = 'C'
        elif final_score >= 40:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'grade': grade,
            'score': round(final_score, 1),
            'summary': f"Overall financial performance grade: {grade} with a score of {final_score:.1f}/100"
        }
    
    def generate_report_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Generate executive summary of analysis results."""
        if not analysis_results.get('performance_grade'):
            return "Analysis results incomplete."
        
        grade = analysis_results['performance_grade']['grade']
        score = analysis_results['performance_grade']['score']
        risk_level = analysis_results['risk_assessment'].get('risk_level', 'Unknown')
        
        # Count insights by priority
        insights = analysis_results.get('insights', [])
        high_priority_insights = sum(1 for i in insights if i.priority == 'High')
        
        # Count top performers
        top_performers = sum(1 for b in analysis_results.get('benchmark_comparisons', []) 
                           if b.performance_level in ['Excellent', 'Good'])
        
        summary = f"""
Executive Financial Analysis Summary

Overall Performance: Grade {grade} ({score}/100)
Risk Level: {risk_level}

Key Highlights:
• {top_performers} metrics performing above industry standards
• {high_priority_insights} high-priority areas requiring attention

{grade_mapping := {'A+': 'Outstanding', 'A': 'Excellent', 'A-': 'Very Good', 
                   'B+': 'Good', 'B': 'Satisfactory', 'B-': 'Adequate',
                   'C+': 'Fair', 'C': 'Needs Improvement', 'D': 'Poor', 'F': 'Critical'}}

Performance Assessment: {grade_mapping.get(grade, 'Unknown')}
        """
        
        return summary.strip()
