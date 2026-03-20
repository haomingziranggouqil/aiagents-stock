"""
智瞰龙虎PDF报告生成模块
"""

from datetime import datetime
import os
import tempfile
import asyncio
import io
from markdown_it import MarkdownIt
import yaml
from pdf_browser_launcher import get_browser_launch_options

# 条件导入pyppeteer，添加异常处理
try:
    from pyppeteer import launch
    has_pyppeteer = True
except (ImportError, OSError) as e:
    # 当pyppeteer无法导入时，使用reportlab作为备选
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    has_pyppeteer = False
    print(f"pyppeteer导入失败，将使用reportlab作为备选: {e}")


class LonghubangPDFGenerator:
    """龙虎榜PDF报告生成器"""
    
    def __init__(self):
        """初始化PDF生成器"""
        pass
    
    def _register_chinese_fonts(self):
        """注册中文字体 - 支持Windows和Linux系统"""
        try:
            # 检查是否已经注册过
            if 'ChineseFont' in pdfmetrics.getRegisteredFontNames():
                return 'ChineseFont'
            
            # Windows系统字体路径
            windows_font_paths = [
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
                'C:/Windows/Fonts/msyh.ttf',    # 微软雅黑（TTF格式）
            ]
            
            # Linux系统字体路径（Docker环境）
            linux_font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # 文泉驿正黑
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # 文泉驿微米黑
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
                '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',  # Noto Serif CJK
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Droid字体
            ]
            
            # 合并所有可能的字体路径
            all_font_paths = windows_font_paths + linux_font_paths
            
            # 尝试注册字体
            for font_path in all_font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        print(f"✅ 成功注册中文字体: {font_path}")
                        return 'ChineseFont'
                    except Exception as e:
                        print(f"⚠️ 尝试注册字体 {font_path} 失败: {e}")
                        continue
            
            # 如果没有找到中文字体，打印警告并使用默认字体
            print("⚠️ 警告：未找到中文字体，PDF中文可能显示为方框")
            print("建议：在Docker中安装中文字体包")
            return 'Helvetica'
        except Exception as e:
            print(f"❌ 注册中文字体时出错: {e}")
            return 'Helvetica'
    
    def _get_chinese_font_css(self):
        """获取中文支持的CSS样式"""
        css_content = """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'WenQuanYi Micro Hei', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0 auto;
            padding: 0;
        }
        
        h1 {
            color: #1f4788;
            text-align: center;
            font-size: 28px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        h2 {
            color: #2c5aa0;
            border-left: 4px solid #1f4788;
            padding-left: 15px;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 20px;
        }
        
        h3 {
            color: #3d6db5;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 18px;
        }
        
        p {
            margin-bottom: 15px;
            text-align: justify;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th {
            background-color: #1f4788;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        
        td {
            padding: 10px;
            border: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        
        hr {
            border: 0;
            height: 1px;
            background: #ccc;
            margin: 30px 0;
        }
        
        strong {
            font-weight: bold;
        }
        
        em {
            font-style: italic;
        }
        
        ul, ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        
        li {
            margin-bottom: 8px;
        }
        
        .center {
            text-align: center;
        }
        
        .title-page {
            text-align: center;
            margin-top: 100px;
        }
        
        .subtitle {
            font-size: 20px;
            color: #666;
            margin-bottom: 50px;
        }
        
        .info-box {
            margin: 30px 0;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        
        .disclaimer {
            margin: 50px 0 20px 0;
            font-style: italic;
            color: #666;
            text-align: center;
        }
        """
        return css_content
    
    def _generate_markdown_content(self, data: dict) -> str:
        """生成Markdown格式的报告内容"""
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        data_info = data.get('data_info', {})
        summary = data_info.get('summary', {})
        recommended = data.get('recommended_stocks', [])
        agents_analysis = data.get('agents_analysis', {})
        
        # 生成Markdown内容
        markdown_content = f"""
# 智瞰龙虎榜分析报告

## AI驱动的龙虎榜多维度分析系统

---

<div class="center">
**生成时间:** {timestamp}<br/>
**数据记录:** {data_info.get('total_records', 0)} 条<br/>
**涉及股票:** {data_info.get('total_stocks', 0)} 只<br/>
**涉及游资:** {data_info.get('total_youzi', 0)} 个<br/>
**AI分析师:** 5位专业分析师团队<br/>
**分析模型:** DeepSeek AI Multi-Agent System
</div>

<div class="disclaimer">
本报告由AI系统基于龙虎榜公开数据自动生成，仅供参考，不构成投资建议。
市场有风险，投资需谨慎。请投资者独立判断并承担投资风险。
</div>

---

## 一、数据概况

本次分析共涵盖 **{data_info.get('total_records', 0)}** 条龙虎榜记录，
涉及 **{data_info.get('total_stocks', 0)}** 只股票和 
**{data_info.get('total_youzi', 0)}** 个游资席位。

### 资金概况
- 总买入金额: {summary.get('total_buy_amount', 0):,.2f} 元
- 总卖出金额: {summary.get('total_sell_amount', 0):,.2f} 元
- 净流入金额: {summary.get('total_net_inflow', 0):,.2f} 元

"""
        
        # TOP游资
        if summary.get('top_youzi'):
            markdown_content += "\n### 1.1 活跃游资 TOP10\n\n"
            markdown_content += "| 排名 | 游资名称 | 净流入金额(元) |\n"
            markdown_content += "|------|----------|----------------|\n"
            for idx, (name, amount) in enumerate(list(summary['top_youzi'].items())[:10], 1):
                markdown_content += f"| {idx} | {name} | {amount:,.2f} |\n"
        
        # TOP股票
        if summary.get('top_stocks'):
            markdown_content += "\n### 1.2 资金净流入 TOP20 股票\n\n"
            markdown_content += "| 排名 | 股票代码 | 股票名称 | 净流入金额(元) |\n"
            markdown_content += "|------|----------|----------|----------------|\n"
            for idx, stock in enumerate(summary['top_stocks'][:20], 1):
                markdown_content += f"| {idx} | {stock['code']} | {stock['name']} | {stock['net_inflow']:,.2f} |\n"
        
        # 热门概念
        if summary.get('hot_concepts'):
            markdown_content += "\n### 1.3 热门概念 TOP15\n\n"
            concepts_text = ""
            for idx, (concept, count) in enumerate(list(summary['hot_concepts'].items())[:15], 1):
                concepts_text += f"{idx}. {concept} ({count}次)　"
                if idx % 3 == 0:
                    concepts_text += "\n"
            markdown_content += concepts_text
        
        # 推荐股票
        markdown_content += "\n---\n\n## 二、AI推荐股票\n"
        
        if not recommended:
            markdown_content += "\n暂无推荐股票\n"
        else:
            markdown_content += f"\n基于5位AI分析师的综合分析，系统识别出以下 **{len(recommended)}** 只潜力股票，\n"
            markdown_content += "这些股票在资金流向、游资关注度、题材热度等多个维度表现突出。\n"
            
            # 推荐股票表格
            markdown_content += "\n### 2.1 推荐股票列表\n\n"
            markdown_content += "| 排名 | 股票代码 | 股票名称 | 净流入金额 | 确定性 | 持有周期 |\n"
            markdown_content += "|------|----------|----------|------------|--------|----------|\n"
            for stock in recommended[:10]:
                markdown_content += f"| {stock.get('rank', '-')} | {stock.get('code', '-')} | {stock.get('name', '-')} | {stock.get('net_inflow', 0):,.0f} | {stock.get('confidence', '-')} | {stock.get('hold_period', '-')} |\n"
            
            # 详细推荐理由
            markdown_content += "\n### 2.2 推荐理由详解\n\n"
            for stock in recommended[:5]:  # 只详细展示前5只
                markdown_content += f"\n#### {stock.get('rank', '-')}. {stock.get('name', '-')} ({stock.get('code', '-')})\n"
                markdown_content += f"推荐理由: {stock.get('reason', '暂无')}\n"
                markdown_content += f"确定性: {stock.get('confidence', '-')} | 持有周期: {stock.get('hold_period', '-')}\n"
        
        # AI分析师报告
        if agents_analysis:
            markdown_content += "\n---\n\n## 三、AI分析师报告\n\n"
            markdown_content += "本报告由5位AI专业分析师从不同维度进行分析，综合形成投资建议：\n"
            markdown_content += "- **游资行为分析师** - 分析游资操作特征和意图\n"
            markdown_content += "- **个股潜力分析师** - 挖掘次日大概率上涨的股票\n"
            markdown_content += "- **题材追踪分析师** - 识别热点题材和轮动机会\n"
            markdown_content += "- **风险控制专家** - 识别高风险股票和市场陷阱\n"
            markdown_content += "- **首席策略师** - 综合研判并给出最终建议\n\n"
            
            agent_titles = {
                'youzi': '3.1 游资行为分析师',
                'stock': '3.2 个股潜力分析师',
                'theme': '3.3 题材追踪分析师',
                'risk': '3.4 风险控制专家',
                'chief': '3.5 首席策略师综合研判'
            }
            
            for agent_key, agent_title in agent_titles.items():
                agent_data = agents_analysis.get(agent_key, {})
                if agent_data:
                    markdown_content += f"\n### {agent_title}\n\n"
                    analysis_text = agent_data.get('analysis', '暂无分析')
                    # 截断过长的文本
                    if len(analysis_text) > 3000:
                        analysis_text = analysis_text[:3000] + "\n...(内容过长，已截断)"
                    markdown_content += analysis_text + "\n\n"
        
        return markdown_content
    
    async def _markdown_to_pdf_browser(self, markdown_content, output_path):
        """使用无头浏览器将Markdown转换为PDF"""
        # 将Markdown转换为HTML
        md = MarkdownIt()
        html_content = md.render(markdown_content)
        
        # 获取CSS样式
        css_content = self._get_chinese_font_css()
        
        # 完整的HTML结构
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>智瞰龙虎榜分析报告</title>
            <style>
            {css_content}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # 创建临时HTML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
            temp_html.write(full_html)
            temp_html_path = temp_html.name
        
        try:
            # 启动浏览器，禁用信号处理以避免主线程限制
            launch_kwargs = get_browser_launch_options()
            browser = await launch(**launch_kwargs)

            # 创建新页面
            page = await browser.newPage()
            
            # 导航到临时HTML文件
            await page.goto(f'file://{temp_html_path}', waitUntil='networkidle0')
            
            # 生成PDF
            await page.pdf({
                'path': output_path,
                'format': 'A4',
                'margin': {
                    'top': '2cm',
                    'right': '2cm',
                    'bottom': '2cm',
                    'left': '2cm'
                },
                'printBackground': True
            })
            
            # 关闭浏览器
            await browser.close()
            
            print(f"使用浏览器生成PDF成功: {output_path}")
            return True
        except Exception as e:
            print(f"使用浏览器生成PDF失败: {e}")
            raise
        finally:
            # 清理临时文件
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
    
    def generate_pdf(self, result_data: dict, output_path: str = None) -> str:
        """
        生成龙虎榜分析PDF报告
        
        Args:
            result_data: 分析结果数据
            output_path: 输出路径，如果为None则生成临时文件
            
        Returns:
            PDF文件路径
        """
        try:
            # 如果没有指定输出路径，创建临时文件
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"智瞰龙虎报告_{timestamp}.pdf")
            
            # 1. 生成Markdown内容
            markdown_content = self._generate_markdown_content(result_data)
            
            if has_pyppeteer:
                # 使用浏览器生成PDF
                asyncio.run(self._markdown_to_pdf_browser(markdown_content, output_path))
            else:
                # reportlab备用方式生成PDF
                # 注册中文字体
                chinese_font = self._register_chinese_fonts()
                
                # 创建内存中的PDF文档
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
                
                # 获取样式
                styles = getSampleStyleSheet()
                
                # 创建自定义样式
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontName=chinese_font,
                    fontSize=24,
                    spaceAfter=30,
                    alignment=TA_CENTER,
                    textColor=colors.darkblue
                )
                
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontName=chinese_font,
                    fontSize=16,
                    spaceAfter=12,
                    spaceBefore=20,
                    textColor=colors.darkblue
                )
                
                subheading_style = ParagraphStyle(
                    'CustomSubHeading',
                    parent=styles['Heading3'],
                    fontName=chinese_font,
                    fontSize=14,
                    spaceAfter=8,
                    spaceBefore=12,
                    textColor=colors.darkgreen
                )
                
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontName=chinese_font,
                    fontSize=11,
                    spaceAfter=6,
                    alignment=TA_JUSTIFY
                )
                
                # 开始构建PDF内容
                story = []
                
                # 标题
                current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
                story.append(Paragraph("智瞰龙虎榜分析报告", title_style))
                story.append(Paragraph(f"生成时间: {current_time}", normal_style))
                story.append(Spacer(1, 20))
                
                # 简单输出markdown内容，保留基本结构
                story.append(Paragraph("报告内容", heading_style))
                # 截取部分markdown内容显示
                preview_text = markdown_content[:1000] + "\n\n...(内容过长，仅显示部分)"
                story.append(Paragraph(preview_text.replace('\n', '<br/>'), normal_style))
                
                # 生成PDF
                doc.build(story)
                
                # 获取PDF内容并保存到文件
                pdf_content = buffer.getvalue()
                buffer.close()
                
                with open(output_path, 'wb') as f:
                    f.write(pdf_content)
            
            print(f"[PDF] 龙虎榜报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[PDF] 生成失败: {e}")
            import traceback
            traceback.print_exc()
            raise


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎PDF生成模块")
    print("=" * 60)
    
    # 创建测试数据
    test_data = {
        'timestamp': '2024-01-15 18:30:00',
        'data_info': {
            'total_records': 150,
            'total_stocks': 50,
            'total_youzi': 30,
            'summary': {
                'total_buy_amount': 500000000,
                'total_sell_amount': 200000000,
                'total_net_inflow': 300000000,
                'top_youzi': {
                    '92科比': 14455321,
                    '赵老哥': 12000000
                },
                'top_stocks': [
                    {'code': '001337', 'name': '四川黄金', 'net_inflow': 14455321}
                ],
                'hot_concepts': {
                    '黄金概念': 10,
                    '新能源': 8
                }
            }
        },
        'recommended_stocks': [
            {
                'rank': 1,
                'code': '001337',
                'name': '四川黄金',
                'net_inflow': 14455321,
                'reason': '游资大幅买入',
                'confidence': '高',
                'hold_period': '短线'
            }
        ],
        'agents_analysis': {
            'chief': {
                'analysis': '综合分析显示...'
            }
        }
    }
    
    # 生成PDF
    generator = LonghubangPDFGenerator()
    pdf_path = generator.generate_pdf(test_data)
    print(f"\nPDF已生成: {pdf_path}")
