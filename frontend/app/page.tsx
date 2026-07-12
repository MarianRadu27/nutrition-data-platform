import Link from "next/link";

const sectionStyle = {
  margin: "0 auto",
  maxWidth: 1180,
  padding: "72px 24px",
} as const;

const eyebrowStyle = {
  color: "#2d5f4c",
  fontSize: 13,
  fontWeight: 800,
  margin: 0,
  textTransform: "uppercase",
} as const;

const ctaBaseStyle = {
  borderRadius: 8,
  display: "inline-flex",
  fontSize: 15,
  fontWeight: 800,
  padding: "13px 18px",
  textDecoration: "none",
} as const;

export default function HomePage() {
  return (
    <main>
      <section
        style={{
          backgroundImage:
            "url(https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=1800&q=80)",
          backgroundPosition: "center",
          backgroundSize: "cover",
          minHeight: "calc(100vh - 73px)",
          position: "relative",
        }}
      >
        <div
          aria-hidden="true"
          style={{
            backgroundColor: "rgba(10, 21, 17, 0.58)",
            inset: 0,
            position: "absolute",
          }}
        />
        <div
          style={{
            alignItems: "center",
            display: "grid",
            margin: "0 auto",
            maxWidth: 1180,
            minHeight: "calc(100vh - 73px)",
            padding: "48px 24px",
            position: "relative",
          }}
        >
          <div style={{ maxWidth: 760 }}>
            <p
              style={{
                color: "#d7eadf",
                fontSize: 14,
                fontWeight: 800,
                margin: "0 0 18px",
                textTransform: "uppercase",
              }}
            >
              Dietetician | Nutriție aplicată | Date alimentare europene
            </p>
            <h1
              style={{
                color: "#ffffff",
                fontSize: 64,
                lineHeight: 1.02,
                margin: "0 0 22px",
                maxWidth: 760,
              }}
            >
              Teodora Pălii
            </h1>
            <p
              style={{
                color: "#eef5f1",
                fontSize: 21,
                lineHeight: 1.55,
                margin: "0 0 32px",
                maxWidth: 680,
              }}
            >
              Consultații de nutriție și planuri alimentare construite cu grijă,
              susținute de un calculator gratuit de calorii și macronutrienți.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              <Link
                href="#contact"
                style={{
                  ...ctaBaseStyle,
                  backgroundColor: "#ffffff",
                  color: "#17211d",
                }}
              >
                Programează o consultație
              </Link>
              <Link
                href="/calculator"
                style={{
                  ...ctaBaseStyle,
                  border: "1px solid rgba(255,255,255,0.72)",
                  color: "#ffffff",
                }}
              >
                Încearcă calculatorul
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section style={sectionStyle}>
        <div
          style={{
            display: "grid",
            gap: 24,
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          }}
        >
          {[
            ["2", "surse europene importate acum: NEVO și ANSES/Ciqual"],
            ["5", "nutrienți afișați în calculatorul MVP"],
            ["0 lei", "acces gratuit la calculatorul de bază"],
          ].map(([value, label]) => (
            <div
              key={value}
              style={{
                borderTop: "1px solid rgba(23, 33, 29, 0.18)",
                paddingTop: 18,
              }}
            >
              <strong style={{ color: "#2d5f4c", fontSize: 34 }}>{value}</strong>
              <p style={{ color: "#52645b", lineHeight: 1.55, margin: "8px 0 0" }}>
                {label}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section
        style={{
          ...sectionStyle,
          display: "grid",
          gap: 38,
          gridTemplateColumns: "minmax(0, 0.9fr) minmax(0, 1.1fr)",
        }}
      >
        <div>
          <p style={eyebrowStyle}>Pentru pacienți și clienți</p>
          <h2 style={{ fontSize: 40, lineHeight: 1.15, margin: "12px 0 18px" }}>
            Un spațiu digital pentru decizii alimentare mai clare.
          </h2>
        </div>
        <div style={{ color: "#4d5f56", fontSize: 18, lineHeight: 1.75 }}>
          <p style={{ marginTop: 0 }}>
            Site-ul va combina prezentarea serviciilor de dietetică cu un
            calculator practic de nutrienți. Utilizatorii pot căuta alimente,
            pot adăuga grame și pot vedea rapid calorii, proteine,
            carbohidrați, grăsimi și fibre.
          </p>
          <p>
            Prima versiune folosește date importate din NEVO și ANSES/Ciqual,
            iar extensiile precum media între surse, micronutrienți suplimentari
            și baze de date noi vor fi adăugate treptat.
          </p>
        </div>
      </section>

      <section
        id="servicii"
        style={{
          backgroundColor: "#ffffff",
          borderTop: "1px solid rgba(23, 33, 29, 0.08)",
        }}
      >
        <div style={sectionStyle}>
          <p style={eyebrowStyle}>Servicii</p>
          <h2 style={{ fontSize: 40, lineHeight: 1.15, margin: "12px 0 28px" }}>
            Suport nutrițional adaptat obiectivelor tale.
          </h2>
          <div
            style={{
              display: "grid",
              gap: 18,
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            }}
          >
            {[
              [
                "Consultație inițială",
                "Evaluare, obiective și direcție nutrițională clară.",
              ],
              [
                "Plan alimentar",
                "Recomandări structurate pentru rutina ta zilnică.",
              ],
              [
                "Monitorizare lunară",
                "Ajustări și suport pentru progres sustenabil.",
              ],
            ].map(([title, text]) => (
              <article
                key={title}
                style={{
                  border: "1px solid rgba(23, 33, 29, 0.12)",
                  borderRadius: 8,
                  padding: 22,
                }}
              >
                <h3 style={{ fontSize: 22, margin: "0 0 10px" }}>{title}</h3>
                <p style={{ color: "#52645b", lineHeight: 1.6, margin: 0 }}>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="blog" style={sectionStyle}>
        <p style={eyebrowStyle}>Blog</p>
        <h2 style={{ fontSize: 36, lineHeight: 1.18, margin: "12px 0 14px" }}>
          Articolele vor fi pregătite într-o etapă următoare.
        </h2>
        <p style={{ color: "#52645b", fontSize: 18, lineHeight: 1.7, maxWidth: 760 }}>
          Pentru MVP, blogul rămâne o secțiune simplă. Mai târziu poate deveni
          o zonă completă cu articole despre alimentație echilibrată,
          interpretarea etichetelor și exemple de mese.
        </p>
      </section>

      <section
        id="contact"
        style={{
          backgroundColor: "#17211d",
          color: "#ffffff",
        }}
      >
        <div
          style={{
            ...sectionStyle,
            alignItems: "center",
            display: "flex",
            flexWrap: "wrap",
            gap: 24,
            justifyContent: "space-between",
          }}
        >
          <div style={{ maxWidth: 680 }}>
            <p
              style={{
                color: "#a8d6bf",
                fontSize: 13,
                fontWeight: 800,
                margin: 0,
                textTransform: "uppercase",
              }}
            >
              Programare
            </p>
            <h2 style={{ fontSize: 38, lineHeight: 1.18, margin: "12px 0 10px" }}>
              Pregătit pentru o consultație?
            </h2>
            <p style={{ color: "#d6e0db", fontSize: 18, lineHeight: 1.65, margin: 0 }}>
              În prima versiune putem conecta aici formularul sau metoda reală
              de programare aleasă pentru cabinet.
            </p>
          </div>
          <a
            href="mailto:contact@dieteticianteodora.ro"
            style={{
              ...ctaBaseStyle,
              backgroundColor: "#ffffff",
              color: "#17211d",
            }}
          >
            contact@dieteticianteodora.ro
          </a>
        </div>
      </section>
    </main>
  );
}
