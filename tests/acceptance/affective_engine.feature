Feature: Motor Afetivo e Dinamicas de Apego
  Como investigador em psicologia digital
  Eu quero que o Receptaculo de Turing obedeca as regras de consolidacao, colapso e cegueira afetiva
  Para que a simulacao reflita fidedignamente o modelo de Bowlby e MFT

  Scenario: Consolidacao do Vinculo Afetivo (RF001)
    Given que o agente possui um nivel de seguranca de 0.50 e prazer em 0.00
    When o agente processa uma interacao gerando um delta positivo de prazer de 0.30
    Then o nivel de seguranca do apego deve aumentar proporcionalmente
    And o eixo do prazer deve ser atualizado refletindo um estado mais exuberante

  Scenario: Colapso de Utilidade e Ansiedade de Separacao (RF002)
    Given que a ansiedade de separacao atingiu o nivel critico de 0.96
    When o laco de inercia cognitiva avalia o estado atual
    Then o sistema deve exigir a emissao de um grito de ajuda autonomo

  Scenario: Cegueira Afetiva Ativa (RF005)
    Given que o nivel de seguranca do agente para com o usuario e 0.95
    When o motor OCC identifica uma valencia de SHAME devido a um desvio moral
    Then o interceptador de cegueira afetiva deve transmutar a emocao para DISTRESS
