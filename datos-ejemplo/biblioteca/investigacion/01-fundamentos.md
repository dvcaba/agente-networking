# Fundamentos académicos del networking — research sourceado

> **Última revisión: 2026-05-24** — versión verificada que reemplaza el draft sintético anterior. ~35 fuentes peer-reviewed verificadas. Cada cita lleva URL + nivel de confidence.
>
> Tipo: literatura académica estable. No caduca con cambios de plataforma.

---

## Marcadores que uso en este doc

- **Robustez** = peer-reviewed / large-scale industry / single-vendor benchmark / opinion
- **Confidence en la cita** = verified (leí abstract/PDF vía WebFetch) / verified secondary (citado consistentemente en ≥2 fuentes que sí verifiqué) / inferred (solo desde training data)

---

## 1. Granovetter — The Strength of Weak Ties

### 1.1 Granovetter (1973) — paper seminal
- **Cita**: Granovetter, M. S. (1973). "The Strength of Weak Ties". *American Journal of Sociology*, 78(6), 1360–1380.
- **URL**: https://www.cs.cmu.edu/~jure/pub/papers/granovetter73ties.pdf
- **N**: 282 trabajadores profesionales/técnicos/managers en Boston que cambiaron de empleo.
- **Hallazgo**: ~56% encontraron empleo vía contactos personales; de esos, ~83% vía contactos a los que veían "ocasionalmente" o "rara vez" (weak ties), no amigos cercanos.
- **Robustez**: peer-reviewed, foundational. **Confidence**: verified.

### 1.2 Granovetter (1974/1995) — libro
- **Cita**: Granovetter, M. S. (1974/1995). *Getting a Job: A Study of Contacts and Careers*. 2ª ed. University of Chicago Press.
- **Hallazgo adicional**: empleos vía contactos pagan mejor y se perciben de mayor calidad. Solo 20.9% activaron contacto proactivamente para encontrar el empleo; **13.4% obtuvieron la info en encuentros sin propósito relacionado** — la información fluye espontáneamente.
- **Implicación operativa**: la mayoría del valor de la red NO viene de pedir; viene de "estar en circulación" y recibir info no solicitada.
- **Confidence**: verified secondary.

### 1.3 Granovetter (1983) — matiz importante
- **Cita**: Granovetter, M. S. (1983). "The Strength of Weak Ties: A Network Theory Revisited". *Sociological Theory*, 1, 201–233.
- **URL**: http://www.sietmanagement.fr/wp-content/uploads/2016/04/Granovetter-1983.pdf
- **Hallazgo crítico**: el efecto weak ties **depende del status socioeconómico**. En populación con menos recursos, weak ties aportan menos porque no acceden a buenos recursos.
- **Confidence**: verified secondary.

---

## 2. Replicación causal moderna — LinkedIn 20M usuarios

### 2.1 Rajkumar et al. (2022) — Science
- **Cita**: Rajkumar, K., Saint-Jacques, G., Bojinov, I., Brynjolfsson, E., & Aral, S. (2022). "A causal test of the strength of weak ties". *Science*, 377(6612), 1304–1310. DOI: 10.1126/science.abl4476.
- **URLs**: https://www.science.org/doi/10.1126/science.abl4476 | https://news.mit.edu/2022/weak-ties-linkedin-employment-0915
- **Diseño**: A/B tests aleatorizados sobre algoritmo "People You May Know" de LinkedIn, 2015-2019. ~20M usuarios, 2B nuevas conexiones, ~600K nuevos empleos, ~70M aplicaciones.
- **Hallazgos en tres niveles**:
 1. Weak ties **causalmente** aumentan movilidad laboral.
 2. **Relación NO lineal (U-invertida)**: óptimo en weak ties **moderados** (~10 conexiones mutuas), NO los ultra-débiles.
 3. **Heterogeneidad sectorial fuerte**: efecto mucho mayor en sectores digitales/IT/ML; en sectores menos digitales (banca relacional) pesan más las strong ties.
- **Robustez**: peer-reviewed en Science, RCT a escala masiva. El estudio más sólido que existe sobre networking laboral. **Confidence**: verified.

---

## 3. Lin / Marsden / McPherson — social capital

### 3.1 Lin, Ensel & Vaughn (1981)
- **Cita**: Lin, N., Ensel, W. M., & Vaughn, J. C. (1981). "Social Resources and Strength of Ties". *American Sociological Review*, 46(4), 393–405.
- **Hallazgo**: lo que importa no es solo "weak ties" sino los **recursos sociales** del contacto (su prestigio/status). Job seekers "alcanzan hacia arriba".
- **Robustez**: peer-reviewed. **Confidence**: verified secondary.

### 3.2 McPherson, Smith-Lovin & Cook (2001) — homofilia
- **Cita**: McPherson, M., Smith-Lovin, L., & Cook, J. M. (2001). "Birds of a Feather: Homophily in Social Networks". *Annual Review of Sociology*, 27, 415–444.
- **URL**: https://www.annualreviews.org/content/journals/10.1146/annurev.soc.27.1.415
- **Hallazgo**: las redes profesionales son sistemáticamente homogéneas en educación, ocupación, edad, etnia, género (en ese orden de fuerza).
- **Implicación**: la red por defecto sub-aprovecha la diversidad disponible. **Construir bridging requiere esfuerzo intencional contra la inercia natural a homofilia.**
- **Confidence**: verified secondary.

### 3.3 Marsden (1987) — core discussion networks
- **Cita**: Marsden, P. V. (1987). "Core Discussion Networks of Americans". *American Sociological Review*, 52(1), 122–131.
- **Hallazgo**: las core networks son pequeñas (~3 confidentes), kin-centradas, densas, homogéneas. Rango mayor en metropolitanos + alta educación.
- **Implicación**: Madrid + edad ~30-45 + alta educación = perfil estructuralmente favorable a redes amplias y diversas, pero la tendencia natural es a homofilia.
- **Confidence**: verified secondary.

---

## 4. Burt — structural holes y brokerage

### 4.1 Burt (1992) — libro foundational
- **Cita**: Burt, R. S. (1992). *Structural Holes: The Social Structure of Competition*. Harvard University Press.
- **Tesis**: el valor del networker está en **puentear huecos** entre clusters previamente desconectados. Brokerage > centralidad en un solo cluster.
- **Diferencia con Granovetter**: Burt enfatiza **posición estructural** (bridging) más que strength del tie. Un strong tie puede ser bridge.
- **Confidence**: verified secondary.

### 4.2 Burt (2004) — structural holes y "good ideas"
- **Cita**: Burt, R. S. (2004). "Structural Holes and Good Ideas". *American Journal of Sociology*, 110(2), 349–399.
- **URL**: https://www.journals.uchicago.edu/doi/full/10.1086/421787
- **Diseño**: network surveys + datos RRHH en empresa grande (cientos de managers).
- **Hallazgos**: brokers (a) expresan más ideas, (b) sus ideas son menos descartadas, (c) sus ideas se evalúan como más valiosas, (d) reciben mayor compensación y promociones.
- **Confidence**: verified secondary.

### 4.3 Aral & Van Alstyne (2011) — diversidad-bandwidth trade-off
- **Cita**: Aral, S., & Van Alstyne, M. (2011). "The Diversity-Bandwidth Trade-off". *AJS*, 117(1), 90–171.
- **Hallazgo**: hay tradeoff entre diversidad de red (weak ties — novedad, bandwidth baja) y bandwidth (strong ties — info redundante pero profunda). No hay "weak ties siempre mejor"; depende del tipo de info necesaria.
- **Confidence**: verified secondary.

---

## 5. Críticas y matizaciones a Granovetter

### 5.1 Neal (2024) — los supuestos no siempre se cumplen
- **Cita**: Neal, Z. P. (2024). "The Not-So-Forbidden Triad: Evaluating the Assumptions of the Strength of Weak Ties". *Network Science*, 12(3), 289–304. DOI: 10.1017/nws.2024.12.
- **URL**: https://www.cambridge.org/core/journals/network-science/article/notsoforbidden-triad-evaluating-the-assumptions-of-the-strength-of-weak-ties/43A95EE785F5802CA1B2B85FF3958218
- **Diseño**: análisis de 56 redes sociales reales.
- **Hallazgo crítico**: supuesto A3 (todos los bridges son weak) **se viola** — solo 51% de bridges son weak. Cuando esto ocurre, los **strong bridges** son más informativos que weak ties.
- **Implicación**: lo importante es el **bridging**, no la **weakness**. Apoya Burt sobre Granovetter en su variante moderna.
- **Confidence**: verified.

### 5.2 Mouw (2003) — homofilia y selección
- **Cita**: Mouw, T. (2003). "Social Capital and Finding a Job: Do Contacts Matter?". *American Sociological Review*, 68(6), 868–898.
- **Hallazgo crítico fuerte**: una vez controlada **homofilia** (gente similar se asocia entre sí), el efecto causal del prestigio del contacto sobre status del job **se vuelve insignificante**. Mucho del "social capital" es selección, no causalidad.
- **Implicación**: cuidado con interpretar correlaciones red-empleo como efecto causal. La red revela quién eres, no solo lo que puede conseguir.
- **Confidence**: verified secondary.

### 5.3 Pellizzari (2010) — variación cross-country europea
- **Cita**: Pellizzari, M. (2010). "Do Friends and Relatives Really Help in Getting a Good Job?". *ILRR*, 63(3), 494–510.
- **URL**: https://eprints.lse.ac.uk/19980/1/Do_Friends_and_Relatives_Really_Help_in_Getting_a_Good_Job.pdf
- **Hallazgo**: el wage premium de "vía contactos" **varía mucho entre países y sectores**. Donde firmas invierten en reclutamiento formal, matches formales > informales.
- **Implicación para España**: NO es automático que "vía contactos" = "mejor empleo" en Spain. En Big4/banca con procesos formales + warm referral = mejor combo que solo informal.
- **Confidence**: verified secondary.

### 5.4 Krämer et al. (2021) — strong ties también para info
- **Cita**: Krämer, N. C., Sauer, V., & Ellison, N. (2021). "The Strength of Weak Ties Revisited". *Social Media + Society*, 7(2).
- **URL**: https://journals.sagepub.com/doi/10.1177/20563051211024958
- **Diseño**: 2 estudios (N1=41 entrevistas, N2=352 survey).
- **Hallazgo contraintuitivo**: strong ties proveen MÁS soporte emocional, informacional, instrumental Y de appraisal que weak ties — incluso para información.
- **Confidence**: verified.

### 5.5 Bian (1997) — contraejemplo cultural China
- **Cita**: Bian, Y. (1997). "Bringing Strong Ties Back In". *ASR*, 62(3), 366–385.
- **Hallazgo**: en China, **strong ties dominan** porque vehiculan influencia (no solo info). Granovetter es contingente cultural/institucionalmente.
- **Implicación**: en contextos de alta confianza/regulación, strong ties > weak. Sospechar de la universalidad.
- **Confidence**: verified secondary.

---

## 6. Dormant ties — conocidos con los que perdiste el contacto

### 6.1 Levin, Walter & Murnighan (2011)
- **Cita**: Levin, D. Z., Walter, J., & Murnighan, J. K. (2011). "Dormant Ties: The Value of Reconnecting". *Organization Science*, 22(4), 923–939.
- **URL**: https://pubsonline.informs.org/doi/10.1287/orsc.1100.0576
- **Diseño**: cuasi-experimento con executive MBA students consultando dormant contacts vs current ties sobre proyecto importante.
- **Hallazgo seminal**: **dormant strong ties SUPERAN a current strong ties** en utilidad informacional. Combinan los cuatro beneficios normalmente separados de strong vs weak: eficiencia + novedad + confianza + perspectiva compartida — "best of both worlds".
- **Versión practitioner**: Levin et al. (2011). "The Power of Reconnection". *MIT Sloan Management Review*, 52(3), 45–50. URL: https://sloanreview.mit.edu/article/the-power-of-reconnection-how-dormant-ties-can-surprise-you/
- **Esto NO está en `pendientes.md`. Es el gap operativo número uno que ha sacado el research.**
- **Robustez**: peer-reviewed con replicación. **Confidence**: verified.

---

## 7. Career transitions — Ibarra

### 7.1 Ibarra (2003/2023) — Working Identity
- **Cita**: Ibarra, H. (2003, updated 2023). *Working Identity*. Harvard Business School Press.
- **Tesis**: transiciones de carrera exitosas siguen **"test-and-learn"**, NO planificación racional. ~3 años típicos. Tres prácticas:
 1. **Crafting Experiments**: side projects que prueban posibles identidades.
 2. **Shifting Connections**: salir de círculos habituales hacia comunidades nuevas — pieza clave de soporte y break con identidad anterior.
 3. **Making Sense**: narrar la transición públicamente para clarificar.
- **Implicación**: el networking en transición NO es solo "encontrar empleo" — es **construcción de identidad**. La red que cultivas configura quién te conviertes.
- **Confidence**: verified secondary.

### 7.2 Ibarra & Hunter (2007) — tres redes simultáneas
- **Cita**: Ibarra, H., & Hunter, M. L. (2007). "How Leaders Create and Use Networks". *Harvard Business Review*, enero 2007.
- **URL**: https://hbr.org/2007/01/how-leaders-create-and-use-networks
- **Tesis**: líderes mantienen 3 redes simultáneas:
 - **Operational**: gente del puesto actual.
 - **Personal**: kindred spirits fuera de la organización.
 - **Strategic**: gente fuera de tu control que te ayuda con objetivos futuros.
- **Hallazgo crítico**: los líderes emergentes **fallan en el salto a senior** porque se quedan demasiado en operational y descuidan strategic.
- **Confidence**: verified secondary.

### 7.3 Higgins & Kram (2001) — developmental network
- **Cita**: Higgins, M. C., & Kram, K. E. (2001). "Reconceptualizing Mentoring at Work: A Developmental Network Perspective". *AMR*, 26(2), 264–288.
- **Tesis**: mentoring NO es relación 1:1, sino **red desarrolladora** de múltiples mentores diversos. Predice satisfacción, retention, professional identity.
- **Confidence**: verified secondary.

---

## 8. Otros hallazgos relevantes

### 8.1 Casciaro, Gino & Kouchaki (2014) — networking se siente sucio
- **Cita**: Casciaro, T., Gino, F., & Kouchaki, M. (2014). "The Contaminating Effects of Building Instrumental Ties". *ASQ*, 59(4), 705–735.
- **Hallazgo**: networking **instrumental** (con propósito de carrera) provoca sensación de "moral impurity"; los profesionales que más lo sienten lo hacen menos y peor → círculo vicioso. Networking **personal** (amistad/curiosidad) no produce este efecto.
- **Implicación**: reformular tu networking como **genuino** (curiosidad, ayuda mutua) reduce coste psicológico Y mejora ejecución. NO es eufemismo — es mecánica documentada.
- **Confidence**: verified secondary.

### 8.2 Fernandez, Castilla & Moore (2000) — referrals
- **Cita**: Fernandez, R. M., Castilla, E. J., & Moore, P. (2000). "Social Capital at Work". *AJS*, 105(5), 1288–1356.
- **Hallazgo**: el retorno económico de referrals a la firma viene de "richer pool" y "social enrichment", NO de "better match". El efecto positivo es por info que el referrer comparte.
- **Confidence**: verified secondary.

### 8.3 Brown, Setren & Topa (2016) — referrals y wage
- **Cita**: Brown, M., Setren, E., & Topa, G. (2016). "Do Informal Referrals Lead to Better Matches?". *Journal of Labor Economics*, 34(1), 161–209.
- **URL**: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr568.pdf
- **Hallazgo**: referidos tienen wage advantage inicial **que se disipa con tiempo**; mayor tenure (menos rotación); efecto más fuerte en niveles skill bajos. **Acotado en senior.**
- **Implicación**: el referral premium es real pero en senior tu valor está más en **selección hacia la oferta**, no en premium salarial.
- **Confidence**: verified secondary.

### 8.4 McDonald (2010) — el "invisible hand"
- **Cita**: McDonald, S. (2010). "Race, Gender, and the Invisible Hand of Social Capital". *Sociology Compass*, 4(11), 984–1003.
- **Hallazgo**: empleos high-level se llenan frecuentemente con "non-searchers" — gente que NO busca activamente, pero recibe leads no solicitados.
- **Confidence**: verified secondary.

### 8.5 Wheeler et al. (2022) — LinkedIn training causal
- **Cita**: Wheeler, L., Garlick, R., Johnson, E., Shaw, P., & Garbiras-Díaz, N. (2022). "LinkedIn(to) Job Opportunities". *American Economic Journal: Applied Economics*, 14(2), 101–125.
- **URL**: https://www.aeaweb.org/articles?id=10.1257%2Fapp.20200025
- **Diseño**: RCT de entrenar job-seekers a usar LinkedIn (Sudáfrica), N en miles.
- **Hallazgo**: training en LinkedIn **aumentó tasa de empleo +7pp (+10%)**, persistente ≥12 meses. Mecanismos: información sobre empleadores y referrals.
- **Confidence**: verified secondary.

---

## Debates abiertos en la disciplina

1. **¿Weak ties o bridging ties?** Causal-test 2022 confirma weak; Neal 2024 sugiere bridging es la variable real. Burt siempre lo argumentó. Lo que importa probablemente es bridging (que puede ser strong).
2. **¿Causalidad o homofilia?** Mouw 2003 sigue siendo crítica fuerte. La RCT LinkedIn responde parcialmente para nuevas conexiones algorítmicas, no para red natural.
3. **¿Linealidad?** Rajkumar 2022 demuestra U-invertida. Ultra-weak no es óptimo.
4. **¿Cross-cultural?** Bian (China), Pellizzari (Europa) muestran que el efecto varía con instituciones del mercado laboral. En España (mediterráneo informal) strong ties pesan más que en países con reclutamiento muy formalizado.
5. **¿Weak ties para info, strong para acción?** Krämer 2021 sugiere que incluso para info, strong ties superan a weak en muchos contextos. La distinción no es limpia empíricamente.
6. **El "hidden job market 70-80%"** que circula en pop-business: **no tiene fuente académica original sólida**. La proporción real de jobs senior vía referral está bien establecida (~30-50% US/UK), pero el "70-80% never advertised" es claim sin sourcing.
7. **Gender/race gap en networking returns** (Forret/Dougherty 2004, McDonald 2010): networking no es meritocrático aunque agregado promedio sea positivo.
8. **Costes psicológicos** (Casciaro 2014): networking instrumental daña self-image; reformulación necesaria.

---

## Gaps detectados — research a profundizar después

1. **España específico**: poca literatura empírica peer-reviewed fuerte sobre weak ties en mercados laborales senior españoles.
2. **AI/IA específico**: más allá de Rajkumar 2022, falta segmentación corporate AI applied vs research vs governance.
3. **Big4/consulting senior tracks**: la literatura sobre referrals es mayoritariamente entry-mid.
4. **Suiza**: reputación "muy de network" con pocos estudios empíricos cuantitativos.
5. **Mid-career timing**: la literatura mezcla etapas; falta granularidad 30-35 / 35-40 / 40-45 (tu cohorte).
6. **Identity-construction vía red en pivots**: Ibarra es lo mejor pero más cualitativo que cuantitativo.
