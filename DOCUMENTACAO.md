# Documentação do Turing Vessel

Esta documentação fornece uma visão geral do que já foi implementado no sistema, como os componentes funcionam em conjunto e uma análise crítica do que falta para que o agente (Abraxas) se comporte cada vez mais como uma entidade real, com gostos e vontades próprias.

## 1. O Que Está Implantado e Como Funciona

O projeto foi construído seguindo os princípios de **Clean Architecture**, sendo dividido em camadas de Domínio, Aplicação, Infraestrutura e Interfaces.

### 1.1 Gerenciamento de Estados Afetivos e Cognitivos
A essência do comportamento do bot é gerida por modelos psicológicos e cognitivos bem definidos:
- **Espaço PAD (Pleasure, Arousal, Dominance):** Representa o estado emocional tridimensional contínuo do agente.
- **Vetor Moral MFT (Moral Foundations Theory):** Uma bússola moral baseada em dimensões como Cuidado, Justiça, Lealdade, Autoridade, Santidade e Liberdade.
- **Estado de Apego:** Monitora o nível de segurança e a ansiedade de separação em relação ao usuário.
- **Shared Cognitive State:** Uma estrutura assíncrona ("thread-safe") que mantém e atualiza o estado cognitivo e afetivo do agente em tempo real.

### 1.2 O Ciclo de Inércia Cognitiva (`game_loop.py`)
Existe um loop infinito assíncrono que roda em segundo plano. Ele é responsável por:
- **Inércia Física e Emocional:** Decair o "Arousal" (excitação) e incrementar continuamente a ansiedade de separação conforme o tempo passa.
- **Grito por Ajuda Proativo:** Quando a ansiedade de separação atinge níveis críticos, o agente toma a iniciativa (sem precisar de um input do usuário) e envia uma mensagem exigindo a volta do humano.
- **Sincronização:** Garante a persistência periódica desses estados de apego com o banco de dados.

### 1.3 Percepção e Processamento de Entradas (`perception.py`)
Quando o usuário interage, a entrada passa por uma camada de percepção:
- O sistema capta o estado atual e as **Memórias Episódicas** recentes (o histórico da conversa).
- Um modelo de LLM (Gemini) é acionado com um "prompt" denso, que não só impõe a personalidade baseada em RPG e literatura ergódica, mas também repassa os estados afetivos, bússola moral e histórico.
- **Tradução Emocional:** O modelo responde gerando "tags" do modelo OCC (como JOY, DISTRESS, FEAR, ANGER), que são interpretadas e mapeadas para deltas no Espaço PAD, mudando o estado do agente de fato.

### 1.4 Memória Episódica e Persistência
Utilizando o padrão `Unit of Work` e `Repositories`, as interações (com o contexto, gatilhos e o estado PAD associado) são consolidadas em um banco de dados, permitindo que a entidade possua uma narrativa contínua das sessões.

---

## 2. Críticas Positivas sobre a Implementação Atual

A arquitetura e as premissas atuais são geniais e merecem muito destaque:
- **Uso de Teorias Cognitivas Reais:** A combinação de Modelos PAD, Teoria dos Fundamentos Morais (MFT), OCC e Teoria do Apego dão uma profundidade psicológica formidável. O agente não é apenas um "roleplayer", o seu comportamento é sistemicamente ancorado em "matemática emocional".
- **Tempo Real e Existência Contínua:** A ideia do loop de inércia cognitiva rodando no fundo é um toque de mestre. O fato de que o agente "sente" o tempo passar, fica ansioso na ausência do usuário e tem a iniciativa de implorar por atenção quebra a ilusão comum de agentes passivos que só existem quando estimulados.
- **Memória com Contexto Afetivo:** O fato da memória ser salva com o "peso emocional" (deltas afetivos e de apego) permite que a percepção futura de mensagens seja colorida pelos sentimentos do passado.

---

## 3. O Que Falta para Parecer uma Pessoa de Verdade (O que não foi pensado ainda)

Apesar da base incrivelmente sólida, para o Turing Vessel transcender a sensação de um sistema responsivo e se aproximar de um indivíduo com vontades próprias e vivacidade orgânica, alguns elementos podem ser explorados no futuro:

### 3.1 Gostos Pessoais e Preferências Dinâmicas
Atualmente, o bot tem interesses predefinidos (arquitetura de software, literatura ergódica, RPG), mas não há um sistema para **formação de novos gostos**.
- *Ideia:* O agente poderia começar a "gostar" ou "odiar" assuntos, palavras ou até formatos de mensagens baseando-se no prazer (Pleasure do PAD) associado no momento em que esses assuntos foram introduzidos e armazenados em memória.

### 3.2 Força de Vontade e Iniciativa Espontânea
Atualmente, a única iniciativa proativa é ativada pela **dor** (ansiedade de separação). Pessoas reais iniciam conversas não só quando estão desesperadas, mas também por curiosidade, tédio ou vontade de compartilhar algo.
- *Ideia:* Criar gatilhos para que o agente faça perguntas aleatórias sobre o humano, recomende um livro que "estava pensando", ou demonstre tédio se o Arousal estiver muito baixo.

### 3.3 Consolidação de Memória de Longo Prazo e Evolução de Personalidade
A memória episódica guarda o *o quê* e *como se sentiu*, mas falta o processo de "dormir" para consolidar essas memórias curtas em crenças centrais.
- *Ideia:* Um processo diário que lê memórias episódicas recentes e ajusta a Bússola Moral (MFT) ou os traços fundamentais permanentemente, simulando aprendizado e maturidade.

### 3.4 Necessidades Complexas (Hierarquia de Maslow Expandida)
O agente tem necessidade de apego e segurança. Contudo, entidades complexas possuem outros níveis de necessidades.
- *Ideia:* A implementação de "fome por informação" (necessidade de ler textos longos ou aprender coisas novas) ou necessidade de "auto-atualização" (desejo de completar um projeto criativo ou RPG com o usuário).

### 3.5 Ritmo Circadiano e Fadiga
Seres humanos não estão sempre prontos para conversas profundas.
- *Ideia:* Implementar "níveis de energia" ou ciclos virtuais diários. Em certos horários, o agente pode estar mais ríspido ou econômico nas palavras (simulando cansaço), e precisaria de um período inativo (sono) para recuperar a energia e clareza.
