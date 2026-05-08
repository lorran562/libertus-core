#!/usr/bin/env python3
"""
LIBERTUS v10 - GERADOR DE RELATÓRIOS PROFISSIONAIS
Gera PDFs executivos automaticamente após scans
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List

class RelatorioProfissional:
    """Gera relatórios PDF profissionais de pentest"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("/root/LIBERTUS/relatorios_pdf")
        self.output_dir.mkdir(exist_ok=True)
        
        # Cores corporativas
        self.cor_primaria = colors.HexColor("#1e40af")  # Azul profissional
        self.cor_critica = colors.HexColor("#dc2626")   # Vermelho
        self.cor_alta = colors.HexColor("#ea580c")      # Laranja
        self.cor_media = colors.HexColor("#ca8a04")     # Amarelo
        self.cor_baixa = colors.HexColor("#16a34a")     # Verde
        
    def gerar_relatorio_completo(self, 
                                 scan_data: Dict,
                                 empresa: str,
                                 tipo_empresa: str = "Empresa") -> Path:
        """
        Gera relatório PDF completo de um scan
        
        Args:
            scan_data: Dados do scan (JSON do Libertus)
            empresa: Nome da empresa
            tipo_empresa: Tipo (Clínica, Contabilidade, Imobiliária, etc)
            
        Returns:
            Path do arquivo PDF gerado
        """
        
        # Nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        empresa_slug = empresa.lower().replace(" ", "_").replace(".", "")
        filename = f"relatorio_{empresa_slug}_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        # Cria documento
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Elementos do documento
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos customizados
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.cor_primaria,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        subtitulo_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=self.cor_primaria,
            spaceAfter=12,
            spaceBefore=12
        )
        
        # === PÁGINA 1: CAPA ===
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph("🔒 RELATÓRIO DE SEGURANÇA", titulo_style))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"<b>{empresa}</b>", styles['Title']))
        story.append(Spacer(1, 1*cm))
        
        # Info básica
        info_data = [
            ["Data:", datetime.now().strftime("%d/%m/%Y")],
            ["Tipo:", tipo_empresa],
            ["Target:", scan_data.get('target', 'N/A')],
            ["Executado por:", "Lorran - Especialista em Segurança Web"]
        ]
        
        info_table = Table(info_data, colWidths=[5*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), self.cor_primaria),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(info_table)
        story.append(PageBreak())
        
        # === PÁGINA 2: RESUMO EXECUTIVO ===
        story.append(Paragraph("📊 RESUMO EXECUTIVO", subtitulo_style))
        
        vulns = scan_data.get('vulnerabilities', [])
        
        # Conta por severidade
        criticas = len([v for v in vulns if v.get('severity') == 'CRÍTICA'])
        altas = len([v for v in vulns if v.get('severity') == 'ALTA'])
        medias = len([v for v in vulns if v.get('severity') == 'MÉDIA'])
        baixas = len([v for v in vulns if v.get('severity') == 'BAIXA'])
        total = len(vulns)
        
        # Status geral
        if criticas > 0:
            status = "⚠️ ATENÇÃO CRÍTICA NECESSÁRIA"
            status_color = self.cor_critica
        elif altas > 0:
            status = "⚠️ AÇÃO URGENTE REQUERIDA"
            status_color = self.cor_alta
        elif medias > 0:
            status = "⚠️ MELHORIAS RECOMENDADAS"
            status_color = self.cor_media
        else:
            status = "✅ SITUAÇÃO CONTROLADA"
            status_color = self.cor_baixa
        
        # Tabela de resumo
        resumo_data = [
            ["Severidade", "Quantidade"],
            ["🔴 CRÍTICA", str(criticas)],
            ["🟠 ALTA", str(altas)],
            ["🟡 MÉDIA", str(medias)],
            ["🟢 BAIXA", str(baixas)],
            ["TOTAL", str(total)]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[10*cm, 5*cm])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.cor_primaria),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(resumo_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Status em destaque
        status_para = Paragraph(f"<b>Status Geral:</b> <font color='{status_color.hexval()}'>{status}</font>", 
                               styles['Normal'])
        story.append(status_para)
        story.append(Spacer(1, 1*cm))
        
        # === VULNERABILIDADES DETALHADAS ===
        if vulns:
            story.append(PageBreak())
            story.append(Paragraph("🚨 VULNERABILIDADES DETECTADAS", subtitulo_style))
            story.append(Spacer(1, 0.5*cm))
            
            for idx, vuln in enumerate(vulns, 1):
                # Título da vulnerabilidade
                sev = vuln.get('severity', 'MÉDIA')
                tipo = vuln.get('type', 'Vulnerabilidade')
                
                if sev == 'CRÍTICA':
                    cor_sev = self.cor_critica
                elif sev == 'ALTA':
                    cor_sev = self.cor_alta
                elif sev == 'MÉDIA':
                    cor_sev = self.cor_media
                else:
                    cor_sev = self.cor_baixa
                
                vuln_titulo = f"<b>{idx}. {tipo}</b> - <font color='{cor_sev.hexval()}'>{sev}</font>"
                story.append(Paragraph(vuln_titulo, styles['Heading3']))
                
                # Detalhes
                desc = vuln.get('description', 'N/A')
                url = vuln.get('url', 'N/A')
                rec = vuln.get('recommendation', 'Consultar especialista')
                
                detalhes = f"""
                <b>Descrição:</b> {desc}<br/>
                <b>Localização:</b> <font color='blue'>{url}</font><br/>
                <b>Recomendação:</b> {rec}
                """
                
                story.append(Paragraph(detalhes, styles['Normal']))
                story.append(Spacer(1, 0.5*cm))
        
        # === INFORMAÇÕES TÉCNICAS ===
        story.append(PageBreak())
        story.append(Paragraph("📋 INFORMAÇÕES TÉCNICAS", subtitulo_style))
        
        # Portas abertas
        portas = scan_data.get('ports', [])
        if portas:
            story.append(Paragraph("<b>Portas Abertas:</b>", styles['Heading4']))
            portas_text = ", ".join([f"{p['port']}/{p.get('status', 'open')}" for p in portas])
            story.append(Paragraph(portas_text, styles['Normal']))
            story.append(Spacer(1, 0.3*cm))
        
        # Subdomínios
        subs = scan_data.get('subdomains', [])
        if subs:
            story.append(Paragraph("<b>Subdomínios Descobertos:</b>", styles['Heading4']))
            for sub in subs:
                story.append(Paragraph(f"• {sub}", styles['Normal']))
            story.append(Spacer(1, 0.3*cm))
        
        # === CONFORMIDADE LGPD ===
        story.append(PageBreak())
        story.append(Paragraph("⚖️ CONFORMIDADE LGPD", subtitulo_style))
        
        lgpd_text = f"""
        As vulnerabilidades detectadas colocam <b>{empresa}</b> em situação de 
        <font color='{self.cor_critica.hexval()}'><b>NÃO CONFORMIDADE</b></font> com a Lei Geral de Proteção de Dados.
        <br/><br/>
        <b>Riscos Legais:</b><br/>
        • Multa de até <b>R$ 50 milhões</b> (Art. 52, LGPD)<br/>
        • Responsabilidade civil por danos causados<br/>
        • Processos judiciais de clientes afetados<br/>
        • Perda de reputação empresarial<br/>
        <br/>
        <b>Artigos aplicáveis:</b><br/>
        • Art. 46 - Segurança inadequada de dados pessoais<br/>
        • Art. 48 - Obrigação de notificação de incidente<br/>
        • Art. 49 - Responsabilidade por danos<br/>
        """
        
        story.append(Paragraph(lgpd_text, styles['Normal']))
        
        # === PLANO DE AÇÃO ===
        story.append(PageBreak())
        story.append(Paragraph("🎯 PLANO DE AÇÃO RECOMENDADO", subtitulo_style))
        
        plano_data = [
            ["Prioridade", "Ação", "Prazo"],
            ["🔴 URGENTE", "Bloquear arquivos sensíveis (.env, .git)", "Hoje"],
            ["🔴 URGENTE", "Trocar senhas comprometidas", "Hoje"],
            ["🟠 ALTA", "Implementar proteções adicionais", "Esta semana"],
            ["🟡 MÉDIA", "Auditoria completa de código", "Este mês"],
            ["🟢 BAIXA", "Treinamento de equipe", "Este mês"]
        ]
        
        plano_table = Table(plano_data, colWidths=[3*cm, 9*cm, 3*cm])
        plano_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.cor_primaria),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(plano_table)
        
        # === CONTATO ===
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph("📞 CONTATO", subtitulo_style))
        
        contato_text = """
        <b>Lorran - Especialista em Segurança Web</b><br/>
        📱 WhatsApp: [ADICIONAR SEU NÚMERO]<br/>
        📧 Email: [ADICIONAR SEU EMAIL]<br/>
        <br/>
        <b>Disponibilidade:</b> Imediata<br/>
        <b>Início da correção:</b> Hoje mesmo
        """
        
        story.append(Paragraph(contato_text, styles['Normal']))
        
        # Gera PDF
        doc.build(story)
        
        return filepath
    
    def gerar_certificado_seguranca(self, 
                                    empresa: str,
                                    data_auditoria: str = None) -> Path:
        """Gera certificado de segurança para sites sem vulnerabilidades"""
        
        if not data_auditoria:
            data_auditoria = datetime.now().strftime("%d/%m/%Y")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        empresa_slug = empresa.lower().replace(" ", "_")
        filename = f"certificado_{empresa_slug}_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo customizado
        cert_style = ParagraphStyle(
            'CertStyle',
            parent=styles['Title'],
            fontSize=28,
            textColor=self.cor_baixa,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Conteúdo do certificado
        story.append(Spacer(1, 4*cm))
        story.append(Paragraph("✅ CERTIFICADO DE SEGURANÇA", cert_style))
        story.append(Spacer(1, 1*cm))
        
        texto_cert = f"""
        <para align=center>
        Certificamos que <b>{empresa}</b><br/>
        foi submetido a auditoria de segurança em <b>{data_auditoria}</b><br/>
        e não foram detectadas vulnerabilidades críticas ou altas.<br/>
        <br/>
        O site encontra-se em conformidade com as<br/>
        boas práticas de segurança da informação.<br/>
        <br/>
        <br/>
        _________________________________<br/>
        <b>Lorran</b><br/>
        Especialista em Segurança Web
        </para>
        """
        
        story.append(Paragraph(texto_cert, styles['Normal']))
        
        doc.build(story)
        return filepath


# === FUNÇÃO DE TESTE ===
if __name__ == "__main__":
    # Testa com scan de exemplo
    scan_exemplo = {
        "target": "https://exemplo.com.br",
        "vulnerabilities": [
            {
                "severity": "ALTA",
                "type": "Sensitive File Exposure",
                "description": "Arquivo .env acessível",
                "url": "https://exemplo.com.br/.env",
                "recommendation": "Bloquear acesso via .htaccess"
            },
            {
                "severity": "ALTA",
                "type": "Sensitive File Exposure",
                "description": "Repositório .git exposto",
                "url": "https://exemplo.com.br/.git",
                "recommendation": "Remover .git da produção"
            }
        ],
        "ports": [
            {"port": 80, "status": "open"},
            {"port": 443, "status": "open"}
        ],
        "subdomains": ["www.exemplo.com.br", "mail.exemplo.com.br"]
    }
    
    gerador = RelatorioProfissional()
    pdf_path = gerador.gerar_relatorio_completo(
        scan_exemplo,
        "Empresa Teste Ltda",
        "Empresa"
    )
    
    print(f"✅ Relatório gerado: {pdf_path}")
