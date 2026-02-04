import re


def format_text_with_bold(text: str) -> str:
    """Convert **text** markdown syntax to HTML <strong>text</strong> tags."""
    if not text:
        return text
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)


def daily_content_template(user_name: str, feed_image: str, feed_text: str, reels_text: str, story_text: str) -> str:
    # Format text with bold markers
    feed_text = format_text_with_bold(feed_text)
    story_text = format_text_with_bold(story_text)
    reels_text = format_text_with_bold(reels_text)
    
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Conteúdo automático diário</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #ffffff;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 40px; text-align: center;">
                            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow Logo" style="width: 114px; height: 32px; margin-bottom: 20px;">
                            <h1 style="margin: 0; color: #8b5cf6; font-size: 24px; font-weight: 600;">
                                {user_name} <span style="color: #ffffff;">chegaram suas ideias para os posts de hoje! 🎉</span>
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <!-- Feed Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 8px 0; color: #8b5cf6; font-size: 20px; font-weight: 600;">Ideia para feed</h2>
                                        <p style="margin: 0 0 20px 0; color: #1e293b; font-size: 16px;">
                                            Copie a legenda e baixe a imagem para colocar no Instagram.
                                        </p>
                                        {f'<img src="{feed_image}" alt="Imagem do Post" style="width: 100%; max-width: 520px; height: auto; border-radius: 8px; margin: 20px 0; display: block;">' if feed_image else '<div style="background-color: #f0f0f0; padding: 40px; text-align: center; border-radius: 8px; margin: 20px 0; color: #888;">Nenhuma imagem disponível</div>'}
                                        <div style="color: #64748b; font-size: 16px; line-height: 1.6; white-space: pre-line;">
                                            {feed_text or 'Nenhum conteúdo de feed foi gerado.'}
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Story Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 8px 0; color: #8b5cf6; font-size: 20px; font-weight: 600;">Ideia para story</h2>
                                        <p style="margin: 0 0 20px 0; color: #1e293b; font-size: 16px;">
                                            Utilize o roteiro para gravar um story para o Instagram.
                                        </p>
                                        <div style="color: #64748b; font-size: 16px; line-height: 1.6; white-space: pre-line;">
                                            {story_text or 'Nenhum conteúdo de story foi gerado.'}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Reels Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 8px 0; color: #8b5cf6; font-size: 20px; font-weight: 600;">Ideia para reels</h2>
                                        <p style="margin: 0 0 20px 0; color: #1e293b; font-size: 16px;">
                                            Utilize o roteiro para gravar um reels para o Instagram.
                                        </p>
                                        <div style="color: #64748b; font-size: 16px; line-height: 1.6; white-space: pre-line;">
                                            {reels_text or 'Nenhum conteúdo de reels foi gerado.'}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Footer Section -->
                            <table role="presentation" style="width: 100%; background-color: #f8fafc; border-radius: 8px; border-top: 1px solid #e2e8f0;">
                                <tr>
                                    <td style="padding: 32px; text-align: center;">
                                        <p style="margin: 0 0 8px 0; color: #64748b; font-size: 14px; font-weight: 500;">
                                            Precisa de ajuda? Entre em contato conosco respondendo este email.
                                        </p>
                                        <p style="margin: 0; color: #6a7282; font-size: 12px; font-weight: 500;">
                                            © 2025 PostNow. Destrave sua criatividade, posts prontos mais rápido que nunca.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>

    </table>
</body>
</html>"""
