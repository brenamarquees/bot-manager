# Vision - Bot de Gestão de Tempo e Projetos

Bem-vindo ao **Vision**, uma IA executiva desenvolvida para transformar a forma como você gerencia seu tempo e organiza seus projetos. Integrado ao Google Calendar e Monday.com, o Vision oferece comandos simples e conselhos personalizados para maximizar sua produtividade.

---

## Descrição

Vision é um bot de Telegram que combina funcionalidades práticas com inteligência artificial. Use comandos como `/schedule` para agendar reuniões ou diga "Estou sobrecarregado" para receber estratégias de gestão de tempo, como a Matriz Eisenhower ou a técnica Pomodoro. Projetado para profissionais multitarefa, Vision é seu parceiro 24/7 para uma rotina mais eficiente.

---

## Funcionalidades

- **Gestão de Agenda:**
  - `/schedule`: Agende eventos no Google Calendar.
  - `/getevent`: Veja eventos do dia.
  - `/freetime`: Liste horários livres.
  - `/busydays`: Identifique os dias mais ocupados do mês.
  - `/clearcalendar`: Liste reuniões para cancelar.

- **Controle de Reuniões:**
  - `/addparticipant`: Adicione participantes.
  - `/removeparticipant`: Remova participantes.
  - `/cancelmeeting`: Cancele uma reunião.
  - `/editmeeting`: Edite data e hora de eventos.

- **Gestão de Tarefas:**
  - `/tasklist`: Liste tarefas pendentes.
  - `/addtask`: Adicione novas tarefas.
  - `/removetask`: Remova tarefas concluídas.
  - `/prioritizetask`: Defina prioridades.

- **Integrações:**
  - `/monday`: Resumo de projetos no Monday.com.

- **Conselhos Personalizados:**
  - Envie mensagens como "Como organizo meu dia?" e receba dicas práticas adaptadas.

---

## Pré-requisitos

Antes de começar, certifique-se de ter:
- Python 3.11+
- Conta no Telegram e um token de bot (obtido via [BotFather](https://t.me/BotFather))
- Credenciais do Google Calendar API (conta de serviço)
- Chave da API Gemini (para IA)
- Acesso ao Monday.com (opcional)

---

## Instalação

1. **Clone o Repositório:**
   ```bash
   git clone https://github.com/seu-usuario/bot-manager.git
   cd bot-manager
   ```

2. **Instale as Dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Crie um `requirements.txt` com: `python-telegram-bot`, `google-api-python-client`, `requests`, `python-dotenv`)*

3. **Configure as Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto:
   ```plaintext
   BOT_TOKEN="seu-token-do-telegram"
   GOOGLE_CREDENTIALS='{"type": "service_account", ...}'
   GEMINI_API_KEY="sua-chave-gemini"
   MONDAY_API_KEY="sua-chave-monday"  # Opcional
   ```

4. **Execute o Bot:**
   ```bash
   python bot.py
   ```

---

## Uso

1. Inicie o bot no Telegram com `/start` para ver a lista de comandos.
2. Use comandos como:
   - `/schedule` para agendar uma reunião.
   - `/tasklist` para ver suas tarefas.
   - `/freetime` para checar horários livres.
3. Envie mensagens sem comandos (ex.: "Tenho muitas tarefas!") para conselhos personalizados.

### Exemplo
- **Comando:** `/schedule`
  - Resposta: "Digite o e-mail do calendário (ex.: 'brena.marques@gmail.com')."
- **Mensagem:** "Como priorizo minhas tarefas?"
  - Resposta: "Use a Matriz Eisenhower: separe o urgente do importante. Quer listar suas tarefas para eu te ajudar?"

---

## Configuração do Google Calendar
1. Crie uma conta de serviço no [Google Cloud Console](https://console.cloud.google.com/).
2. Habilite a Google Calendar API.
3. Compartilhe seu calendário (ex.: `seu-email@gmail.com`) com o `client_email` da conta de serviço, dando permissão de edição.

---

## Contribuição

Quer melhorar o Vision? Siga estes passos:
1. Fork o repositório.
2. Crie uma branch para sua feature:
   ```bash
   git checkout -b minha-feature
   ```
3. Faça commit das suas mudanças:
   ```bash
   git commit -m "Adiciona nova funcionalidade"
   ```
4. Envie um Pull Request.

---

## Licença

Este projeto é licenciado sob a [MIT License](LICENSE).

---

## Contato

Dúvidas ou sugestões? Abra uma issue ou entre em contato com [seu-email@exemplo.com].

---

### **Notas**
- **Personalização:** Substitua `seu-usuario`, `seu-email@exemplo.com` e outros placeholders pelos seus dados reais.
- **Requirements.txt:** Se ainda não tiver, crie um com:
  ```
  python-telegram-bot==20.6
  google-api-python-client==2.93.0
  requests==2.31.0
  python-dotenv==1.0.0
  ```

