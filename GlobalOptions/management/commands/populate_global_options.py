from django.core.management.base import BaseCommand
from django.db import transaction

from GlobalOptions.models import (
    PredefinedFont,
    PredefinedProfession,
    PredefinedSpecialization,
)


class Command(BaseCommand):
    help = 'Popula o banco de dados com profissões, especializações e fontes predefinidas'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando população das opções globais...')

        with transaction.atomic():
            # Criar profissões predefinidas
            professions_data = [
                {
                    'name': 'Advogado',
                    'specializations': [
                        'Tributário', 'Trabalhista', 'Civil', 'Executivo',
                        'Empresarial', 'Constitucional', 'Administrativo',
                        'Penal', 'Ambiental', 'Digital'
                    ]
                },
                {
                    'name': 'Coach',
                    'specializations': [
                        'Executivo', 'Empresarial', 'Financeiro', 'Digital',
                        'Estratégico', 'Pessoal', 'Carreira', 'Liderança', 'Vendas'
                    ]
                },
                {
                    'name': 'Consultor',
                    'specializations': [
                        'Estratégico', 'Financeiro', 'Digital', 'Empresarial',
                        'Marketing', 'Vendas', 'RH', 'Tecnologia'
                    ]
                },
                {
                    'name': 'Médico',
                    'specializations': [
                        'Cardiologia', 'Ortopedia', 'Pediatria', 'Clínica Geral',
                        'Dermatologia', 'Neurologia', 'Psiquiatria', 'Ginecologia', 'Urologia'
                    ]
                },
                {
                    'name': 'Psicólogo',
                    'specializations': [
                        'Psicologia Clínica', 'Psicologia Organizacional',
                        'Psicologia Infantil', 'Psicologia Social',
                        'Psicologia Esportiva', 'Psicologia Forense'
                    ]
                },
                {
                    'name': 'Dentista',
                    'specializations': [
                        'Endodontia', 'Ortodontia', 'Implantodontia',
                        'Periodontia', 'Odontopediatria', 'Cirurgia Oral'
                    ]
                },
                {
                    'name': 'Contador',
                    'specializations': [
                        'Contabilidade Tributária', 'Contabilidade Societária',
                        'Auditoria', 'Controladoria', 'Consultoria', 'Perícia'
                    ]
                },
                {
                    'name': 'Arquiteto',
                    'specializations': [
                        'Arquitetura Residencial', 'Arquitetura Comercial',
                        'Arquitetura Sustentável', 'Urbanismo', 'Interiores', 'Paisagismo'
                    ]
                },
                {
                    'name': 'Designer',
                    'specializations': [
                        'Design Gráfico', 'Design de Produto', 'Design de Interface',
                        'Design de Experiência', 'Design de Moda', 'Design Industrial'
                    ]
                },
                {
                    'name': 'Programador',
                    'specializations': [
                        'Desenvolvimento Web', 'Desenvolvimento Mobile',
                        'Desenvolvimento Desktop', 'Data Science',
                        'Machine Learning', 'DevOps'
                    ]
                },
                {
                    'name': 'Professor',
                    'specializations': [
                        'Educação Infantil', 'Ensino Fundamental', 'Ensino Médio',
                        'Ensino Superior', 'Educação Especial', 'Educação Física'
                    ]
                },
                {
                    'name': 'Fisioterapeuta',
                    'specializations': [
                        'Ortopedia', 'Neurologia', 'Cardiorrespiratória',
                        'Esportiva', 'Pediatria', 'Geriatria'
                    ]
                },
                {
                    'name': 'Nutricionista',
                    'specializations': [
                        'Nutrição Esportiva', 'Nutrição Clínica', 'Nutrição Funcional',
                        'Nutrição Infantil', 'Nutrição Hospitalar'
                    ]
                },
                {
                    'name': 'Personal Trainer',
                    'specializations': [
                        'Musculação', 'Funcional', 'Aeróbico', 'Reabilitação',
                        'Emagrecimento', 'Hipertrofia'
                    ]
                }
            ]

            # Criar fontes predefinidas
            fonts_data = [
                'Inter', 'Roboto', 'Open Sans', 'Poppins', 'Montserrat',
                'Lato', 'Source Sans Pro', 'Nunito', 'Ubuntu', 'Raleway',
                'Playfair Display', 'Merriweather', 'PT Sans', 'Noto Sans', 'Work Sans'
            ]

            # Criar profissões e especializações
            for prof_data in professions_data:
                profession, created = PredefinedProfession.objects.get_or_create(
                    name=prof_data['name'],
                    defaults={'is_active': True}
                )

                if created:
                    self.stdout.write(f'Profissão criada: {profession.name}')
                else:
                    self.stdout.write(
                        f'Profissão já existe: {profession.name}')

                # Criar especializações para a profissão
                for spec_name in prof_data['specializations']:
                    specialization, created = PredefinedSpecialization.objects.get_or_create(
                        name=spec_name,
                        profession=profession,
                        defaults={'is_active': True}
                    )

                    if created:
                        self.stdout.write(
                            f'  - Especialização criada: {specialization.name}')
                    else:
                        self.stdout.write(
                            f'  - Especialização já existe: {specialization.name}')

            # Criar fontes
            for font_name in fonts_data:
                font, created = PredefinedFont.objects.get_or_create(
                    name=font_name,
                    defaults={'is_active': True}
                )

                if created:
                    self.stdout.write(f'Fonte criada: {font.name}')
                else:
                    self.stdout.write(f'Fonte já existe: {font.name}')

        self.stdout.write(
            self.style.SUCCESS(
                'População das opções globais concluída com sucesso!')
        )
