import React from "react";
import "./Styles/main.css";
import TextInput from "./Components/TextInput.jsx";
import { MdArrowBackIosNew } from "react-icons/md";
import Map from "./Components/Map.jsx";
import { useTheme } from "./ThemeContext";
import Llm_chat from "./Llm_chat";
import LoadIndicator from "./Components/LoadIndicator.jsx";
import Markdown from 'react-markdown'
import Vacantes_screen from "./Vacantes_screen";
import Apple_map from "./Components/Apple_map";
import doodleImage1 from "../assets/imagen1.jpg";
import doodleImage2 from "../assets/imagen2.jpg";
import doodleImage3 from "../assets/imagen3.jpg";

// Estados de la aplicación
const SCREEN_STATES = {
  INPUT: "input",           // Pantalla inicial de búsqueda
  LOADING: "loading",       // Cargando resultados
  NO_RESULTS: "no_results", // Sin resultados
  RESULTS: "results"        // Mostrando resultados
};

const SCREEN_STATES2 = {
  MAPA: "mapa",
  PAGINA: "pagina",
  OFERTA: "oferta"
}

export default function Main() {
  const { mode } = useTheme();

  const busquedarapidaitems = [
    "Desarrollador Full Stack React / Node.js",
    "Ingeniero de Redes y Telecomunicaciones",
    "Especialista en Ciberseguridad & SOC",
    "Diseñador UI/UX & Producto Digital"
  ];

  // Datos de prueba para simular la respuesta del backend
  const mockVacantes = [
    {
      id: 1,
      puesto: "Desarrollador Full Stack React / Node.js",
      modalidad: "Remoto",
      sueldo: "65,000 DOP",
      horario: "Lunes a Viernes, 9am - 5pm",
      ubicacion: "Santo Domingo",
      descripcion: "Buscamos un Desarrollador Full Stack con experiencia en React, Node.js y bases de datos relacionales y no relacionales. Participarás en la arquitectura, desarrollo de APIs y optimización de aplicaciones web.",
      beneficios: [
        "Seguro médico privado complementario",
        "Trabajo 100% remoto con horario flexible",
        "Bono anual por desempeño",
        "Presupuesto para cursos y certificaciones"
      ],
      requisitos: [
        "Mínimo 2 años de experiencia desarrollando con React y Node.js",
        "Conocimientos sólidos en bases de datos SQL y NoSQL",
        "Experiencia en consumo y creación de APIs RESTful",
        "Manejo de control de versiones con Git y metodologías ágiles"
      ],
      payload: {
        Puesto: "Desarrollador Full Stack React / Node.js",
        Modalidad: "Remoto",
        Sueldo: "65,000 DOP",
        Horario: "Lunes a Viernes, 9am - 5pm",
        Ubicacion: "Santo Domingo",
        Descripcion: "Buscamos un Desarrollador Full Stack con experiencia en React, Node.js y bases de datos relacionales y no relacionales. Participarás en la arquitectura, desarrollo de APIs y optimización de aplicaciones web.",
        Beneficios: [
          "Seguro médico privado complementario",
          "Trabajo 100% remoto con horario flexible",
          "Bono anual por desempeño",
          "Presupuesto para cursos y certificaciones"
        ],
        Requisitos: [
          "Mínimo 2 años de experiencia desarrollando con React y Node.js",
          "Conocimientos sólidos en bases de datos SQL y NoSQL",
          "Experiencia en consumo y creación de APIs RESTful",
          "Manejo de control de versiones con Git y metodologías ágiles"
        ],
        Direccion: "Av. Winston Churchill, Piantini, Santo Domingo",
        Nombre_Empresa: "Tech Dominicana Labs",
        Numero_Telefono: "809-555-0142",
        Email: "talento@techdominicana.do",
        latitud: 18.4740,
        longitud: -69.9360,
        fecha_publicacion: "2026-09-25"
      }
    },
    {
      id: 2,
      puesto: "Ingeniero de Redes y Telecomunicaciones",
      modalidad: "Presencial",
      sueldo: "55,000 DOP",
      horario: "Lunes a Viernes, 8am - 5pm",
      ubicacion: "Santiago",
      descripcion: "Empresa líder en telecomunicaciones solicita Ingeniero de Redes con certificación CCNA o equivalente. Responsable de configuración de switches, routers, firewalls y monitoreo de enlaces.",
      beneficios: [
        "Seguro de salud para dependientes directos",
        "Plan de bonificación trimestral",
        "Flota corporativa y subsidio de combustible",
        "Oportunidad de desarrollo y crecimiento profesional"
      ],
      requisitos: [
        "Grado universitario en Ingeniería Telemática, Redes o carreras afines",
        "Certificación Cisco CCNA o equivalente vigente",
        "Experiencia mínima de 2 años en administración de switches y routers",
        "Disponibilidad para guardias de soporte técnico y monitoreo"
      ],
      payload: {
        Puesto: "Ingeniero de Redes y Telecomunicaciones",
        Modalidad: "Presencial",
        Sueldo: "55,000 DOP",
        Horario: "Lunes a Viernes, 8am - 5pm",
        Ubicacion: "Santiago",
        Descripcion: "Empresa líder en telecomunicaciones solicita Ingeniero de Redes con certificación CCNA o equivalente. Responsable de configuración de switches, routers, firewalls y monitoreo de enlaces.",
        Beneficios: [
          "Seguro de salud para dependientes directos",
          "Plan de bonificación trimestral",
          "Flota corporativa y subsidio de combustible",
          "Oportunidad de desarrollo y crecimiento profesional"
        ],
        Requisitos: [
          "Grado universitario en Ingeniería Telemática, Redes o carreras afines",
          "Certificación Cisco CCNA o equivalente vigente",
          "Experiencia mínima de 2 años en administración de switches y routers",
          "Disponibilidad para guardias de soporte técnico y monitoreo"
        ],
        Direccion: "Av. 27 de Febrero, Santiago de los Caballeros",
        Nombre_Empresa: "Telecomunicaciones del Cibao",
        Numero_Telefono: "809-582-9900",
        Email: "empleos@telecomcibao.com.do",
        latitud: 19.4517,
        longitud: -70.6970,
        fecha_publicacion: "2026-09-24"
      }
    },
    {
      id: 3,
      puesto: "Especialista en Ciberseguridad & SOC",
      modalidad: "Híbrido",
      sueldo: "80,000 DOP",
      horario: "Lunes a Viernes, 9am - 6pm",
      ubicacion: "Distrito Nacional",
      descripcion: "Entidad financiera busca analista de seguridad para centro de operaciones SOC, monitoreo de amenazas, análisis de vulnerabilidades y respuesta a incidentes de seguridad de la información.",
      beneficios: [
        "Plan de pensiones complementario",
        "2 días de teletrabajo a la semana",
        "Seguro médico internacional",
        "Bono anual de hasta 2 salarios"
      ],
      requisitos: [
        "Licenciatura en Informática, Ciberseguridad o Ingeniería de Sistemas",
        "Experiencia comprobable en análisis de incidentes de seguridad y SIEM",
        "Certificaciones como CompTIA Security+, CEH o equivalentes",
        "Conocimiento en normativas de seguridad ISO 27001"
      ],
      payload: {
        Puesto: "Especialista en Ciberseguridad & SOC",
        Modalidad: "Híbrido",
        Sueldo: "80,000 DOP",
        Horario: "Lunes a Viernes, 9am - 6pm",
        Ubicacion: "Distrito Nacional",
        Descripcion: "Entidad financiera busca analista de seguridad para centro de operaciones SOC, monitoreo de amenazas, análisis de vulnerabilidades y respuesta a incidentes de seguridad de la información.",
        Beneficios: [
          "Plan de pensiones complementario",
          "2 días de teletrabajo a la semana",
          "Seguro médico internacional",
          "Bono anual de hasta 2 salarios"
        ],
        Requisitos: [
          "Licenciatura en Informática, Ciberseguridad o Ingeniería de Sistemas",
          "Experiencia comprobable en análisis de incidentes de seguridad y SIEM",
          "Certificaciones como CompTIA Security+, CEH o equivalentes",
          "Conocimiento en normativas de seguridad ISO 27001"
        ],
        Direccion: "Av. Abraham Lincoln, Bella Vista, Distrito Nacional",
        Nombre_Empresa: "Banco Digital Caribe",
        Numero_Telefono: "809-567-8899",
        Email: "seleccion@bancodigitalcaribe.do",
        latitud: 18.4550,
        longitud: -69.9500,
        fecha_publicacion: "2026-09-23"
      }
    },
    {
      id: 4,
      puesto: "Diseñador UI/UX & Producto Digital",
      modalidad: "Remoto",
      sueldo: "48,000 DOP",
      horario: "Lunes a Viernes, 9am - 5pm",
      ubicacion: "Santo Domingo",
      descripcion: "Diseño de interfaces intuitivas en Figma, creación de design systems, prototipado interactivo y pruebas de usabilidad con usuarios reales para plataformas web y móviles.",
      beneficios: [
        "Horario flexible",
        "Equipo MacBook Pro proporcionado",
        "Días adicionales libres remunerados"
      ],
      requisitos: [
        "Portafolio de proyectos UI/UX comprobable con casos de estudio",
        "Dominio avanzado de Figma, diseño de componentes y Design Systems",
        "Experiencia en investigación con usuarios y pruebas de usabilidad",
        "Capacidad de comunicación asertiva con equipos de frontend"
      ],
      payload: {
        Puesto: "Diseñador UI/UX & Producto Digital",
        Modalidad: "Remoto",
        Sueldo: "48,000 DOP",
        Horario: "Lunes a Viernes, 9am - 5pm",
        Ubicacion: "Santo Domingo",
        Descripcion: "Diseño de interfaces intuitivas en Figma, creación de design systems, prototipado interactivo y pruebas de usabilidad con usuarios reales para plataformas web y móviles.",
        Beneficios: [
          "Horario flexible",
          "Equipo MacBook Pro proporcionado",
          "Días adicionales libres remunerados"
        ],
        Requisitos: [
          "Portafolio de proyectos UI/UX comprobable con casos de estudio",
          "Dominio avanzado de Figma, diseño de componentes y Design Systems",
          "Experiencia en investigación con usuarios y pruebas de usabilidad",
          "Capacidad de comunicación asertiva con equipos de frontend"
        ],
        Direccion: "Ensanche Naco, Santo Domingo",
        Nombre_Empresa: "Agencia Pixel Creativa",
        Numero_Telefono: "809-222-3344",
        Email: "jobs@pixelcreativa.do",
        latitud: 18.4764,
        longitud: -69.9270,
        fecha_publicacion: "2026-09-22"
      }
    }
  ];

  const mockRespuestaBackend = {
    IA_text: `### Resultados de la Búsqueda 🎯

Hemos identificado las **mejores oportunidades de empleo** disponibles según tu búsqueda:

- **Desarrollador Full Stack**: 100% remoto, excelentes beneficios y tecnologías modernas (React y Node.js).
- **Ingeniero de Redes y Telecomunicaciones**: Puesto presencial en Santiago para gestión de infraestructura empresarial.
- **Especialista en Ciberseguridad & SOC**: Modelo híbrido en el Distrito Nacional para análisis de seguridad y monitoreo.
- **Diseñador UI/UX**: Enfoque en diseño de interfaces y prototipado para productos digitales.

💡 *Selecciona cualquier vacante en la lista para ver la ubicación en el mapa, cálculo de distancia, sueldo y aplicar.*`,
    Vacantes: mockVacantes
  };

  // Estados
  const [inputText, setInputText] = React.useState("");
  const [screenState, setScreenState] = React.useState(SCREEN_STATES.INPUT);
  const [hasSearched, setHasSearched] = React.useState(false);
  const [isSearching, setIsSearching] = React.useState(false);
  const [ofertas, setOfertas] = React.useState(mockRespuestaBackend);
  const [IAButton, setIAButton] = React.useState(false);
  const [verPagina, setVerPagina] = React.useState(SCREEN_STATES2.OFERTA);
  const [ofertaSeleccionada, setOfertaSeleccionada] = React.useState(mockVacantes[0]);
  const [IA_text, setIA_text] = React.useState(null);

  // Escuchar evento del logo para regresar suavemente al estado inicial
  React.useEffect(() => {
    const handleReset = () => {
      setHasSearched(false);
      setIsSearching(false);
      setScreenState(SCREEN_STATES.INPUT);
      setInputText("");
    };
    window.addEventListener("reset-home-search", handleReset);
    return () => window.removeEventListener("reset-home-search", handleReset);
  }, []);

  // Handler para iniciar búsqueda y activar animación de subida
  const handleSearch = (customQuery) => {
    const query = typeof customQuery === "string" ? customQuery : inputText;
    if (typeof customQuery === "string") {
      setInputText(customQuery);
    }
    // Activar inmediatamente el desplazamiento hacia arriba y estado de carga
    setHasSearched(true);
    setIsSearching(true);
    setScreenState(SCREEN_STATES.LOADING);
    fetchResultados(query);
  };

  // Fetch real al backend para obtener los resultados de las vacantes
  const fetchResultados = async (queryTexto) => {
    const query = queryTexto && queryTexto.trim() ? queryTexto.trim() : (inputText.trim() || "desarrollador");
    const startTime = Date.now();

    try {
      const response = await fetch("http://localhost:8000/pruebas_frontend/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: query }),
      });

      // Asegurar que la animación de desplazamiento suave hacia arriba tenga suficiente tiempo (mínimo 550ms)
      const elapsed = Date.now() - startTime;
      if (elapsed < 550) {
        await new Promise((resolve) => setTimeout(resolve, 550 - elapsed));
      }

      if (!response.ok) {
        throw new Error(`Error en el servidor: ${response.status}`);
      }

      const resData = await response.json();
      console.log("Respuesta recibida del backend:", resData);

      if (!resData || resData.datos === "Vacio" || !resData.datos) {
        const qLower = query.toLowerCase();
        // Si coincide con alguna tarjeta o término demo, usar las vacantes demo para visualizar Vacantes_screen
        if (
          qLower.includes("vacante") ||
          qLower.includes("santo domingo") ||
          qLower.includes("pagada") ||
          qLower.includes("desarrollador") ||
          qLower.includes("react") ||
          qLower.includes("full") ||
          qLower.includes("redes") ||
          qLower.includes("ciber") ||
          qLower.includes("diseñador")
        ) {
          setOfertas(mockRespuestaBackend);
          setOfertaSeleccionada(mockVacantes[0]);
          setScreenState(SCREEN_STATES.RESULTS);
          setVerPagina(SCREEN_STATES2.OFERTA);
        } else {
          setScreenState(SCREEN_STATES.NO_RESULTS);
        }
        setIsSearching(false);
        return;
      }

      const payloadDatos = resData.datos;
      const vacantesRaw = payloadDatos.Vacantes || payloadDatos.vacantes || [];

      if (!Array.isArray(vacantesRaw) || vacantesRaw.length === 0) {
        setScreenState(SCREEN_STATES.NO_RESULTS);
        setIsSearching(false);
        return;
      }

      // Normalizar estructura de cada vacante para asegurar compatibilidad con Map y Vacantes_screen
      const vacantesFormateadas = vacantesRaw.map((v, index) => {
        const p = v.payload || v;
        return {
          id: v.id || p.id_oferta || index + 1,
          payload: {
            Puesto: p.Puesto || p.puesto || "Puesto no especificado",
            Modalidad: p.Modalidad || p.modalidad || "Presencial",
            Sueldo: p.Sueldo_Texto || (p.Sueldo ? `${p.Sueldo} DOP` : "A convenir"),
            Horario: p.Horario || p.horario || "Tiempo Completo",
            Ubicacion: p.Ubicacion || p.ubicacion || "Santo Domingo",
            Descripcion: p.Descripcion || p.descripcion || "",
            Beneficios: Array.isArray(p.Beneficios) ? p.Beneficios : (Array.isArray(p.beneficios) ? p.beneficios : ["Beneficios de ley"]),
            Requisitos: p.Requisitos || p.requisitos || (Array.isArray(p.detalles?.requisitos_educativos) ? p.detalles.requisitos_educativos : (p.detalles?.requisitos_educativos ? [p.detalles.requisitos_educativos] : null)),
            Direccion: p.Direccion || p.direccion || p.Ubicacion || "República Dominicana",
            Nombre_Empresa: p.Nombre_Empresa || p.nombre_empresa || p.Empresa || "Empresa Confidencial",
            Numero_Telefono: p.Numero_Telefono || p.numero_telefono || "No especificado",
            Email: p.Email || p.email || "No especificado",
            URL: p.URL || p.url || "",
            url_postular: p.url_postular || "",
            latitud: p.latitud ?? p.lat ?? null,
            longitud: p.longitud ?? p.lng ?? p.lon ?? null,
            sector: p.sector || null,
            fecha_publicacion: p.fecha_publicacion || p.fecha || p.Fecha || "Reciente"
          }
        };
      });

      const nuevaRespuesta = {
        IA_text: payloadDatos.IA_text || `### Resultados de la Búsqueda 🎯\n\nHemos identificado **${vacantesFormateadas.length} vacantes** disponibles para tu búsqueda de **${query}**.\n\n💡 *Selecciona cualquier vacante en la lista para ver la ubicación en el mapa, cálculo de distancia, sueldo y aplicar.*`,
        Vacantes: vacantesFormateadas
      };

      setOfertas(nuevaRespuesta);
      setOfertaSeleccionada(vacantesFormateadas[0]);
      setScreenState(SCREEN_STATES.RESULTS);
      setVerPagina(SCREEN_STATES2.OFERTA);
      setIsSearching(false);
    } catch (error) {
      console.error("Error al obtener vacantes del backend:", error);
      const elapsed = Date.now() - startTime;
      if (elapsed < 550) {
        await new Promise((resolve) => setTimeout(resolve, 550 - elapsed));
      }
      // Fallback a datos mock si el backend no responde
      setOfertas(mockRespuestaBackend);
      setOfertaSeleccionada(mockVacantes[0]);
      setScreenState(SCREEN_STATES.RESULTS);
      setVerPagina(SCREEN_STATES2.OFERTA);
      setIsSearching(false);
    }
  };

  const renderOfertas = () => {
    switch (verPagina) {
      case SCREEN_STATES2.OFERTA:
        return (
          <div id="Job-Search-Frame2">
            {ofertaSeleccionada ? (
              <Vacantes_screen ofertaSeleccionada={ofertaSeleccionada} />
            ) : (
              "Selecciona una oferta para verla aquí"
            )}
          </div>
        );
      case SCREEN_STATES2.PAGINA:
        return (
          <iframe
            id="Job-Search-Frame2"
            src={ofertaSeleccionada ? ofertaSeleccionada.payload.URL : ""}
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals"
            title="Job Search"
          ></iframe>
        );
      case SCREEN_STATES2.MAPA:
        return <Apple_map ofertaSeleccionada={ofertaSeleccionada} />;
    }
  };

  const renderContent = () => {
    if (screenState === SCREEN_STATES.NO_RESULTS) {
      return (
        <Llm_chat
          SCREEN_STATES={SCREEN_STATES}
          setOfertas={setOfertas}
          setScreenState={(st) => {
            if (st === SCREEN_STATES.INPUT) {
              setHasSearched(false);
            }
            setScreenState(st);
          }}
          handleSearch={handleSearch}
          set_vacio={true}
        />
      );
    }

    return (
      <div
        id="Search-Master-Layout"
        className={`search-master-layout ${hasSearched ? "is-at-top" : "is-at-center"}`}
      >
        {/* Contenedor animado del TextInput que sube suavemente hacia arriba */}
        <div id="Text-Input-Section" className={hasSearched ? "section-top" : "section-center"}>
          <h1 id="front-panel-title">Que empleo buscas?</h1>

          <div id="Top-Front-Panel-Bar-Container">
            <div className="IA-Text-Container-Bottom">
              <TextInput
                inputText={inputText}
                setInputText={setInputText}
                setSearchButton={() => handleSearch()}
                loading={isSearching}
              />
            </div>
          </div>

          {/* Tarjetas de búsqueda rápida en el estado inicial central */}
          <div className="Input-Cards-Section">
            <label className="Input-Cards-Section-Label">Búsqueda rápida</label>
            <div className="Input-Cards-Container">
              <div
                className="Input-Card"
                onClick={() => {
                  setInputText("Vacantes nuevas");
                  handleSearch("Vacantes nuevas");
                }}
                style={{ cursor: "pointer" }}
              >
                <div className="Input-Card-Text">
                  <h3 className="Input-Card-Title">Vacantes nuevas</h3>
                  <p className="Input-Card-Subtitle">Vacantes de hoy</p>
                </div>
                <div className="Input-Card-Image-Space1">
                  <img src={doodleImage1} alt="Vacantes nuevas" className="Input-Card-Image" />
                </div>
              </div>
              <div
                className="Input-Card"
                onClick={() => {
                  setInputText("Santo Domingo");
                  handleSearch("Santo Domingo");
                }}
                style={{ cursor: "pointer" }}
              >
                <div className="Input-Card-Text">
                  <h3 className="Input-Card-Title">Vacantes cerca de ti</h3>
                  <p className="Input-Card-Subtitle">Vacantes a solo 10 minutos de tu lugar</p>
                </div>
                <div className="Input-Card-Image-Space2">
                  <img src={doodleImage2} alt="" className="Input-Card-Image" />
                </div>
              </div>
              <div
                className="Input-Card"
                onClick={() => {
                  setInputText("Mejores pagadas");
                  handleSearch("Mejores pagadas");
                }}
                style={{ cursor: "pointer" }}
              >
                <div className="Input-Card-Text">
                  <h3 className="Input-Card-Title">Mejores pagadas</h3>
                  <p className="Input-Card-Subtitle">300 usuarios encontraron puestos aquí</p>
                </div>
                <div className="Input-Card-Image-Space3">
                  <img src={doodleImage3} alt="" className="Input-Card-Image" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sección de resultados de búsqueda que muestra Vacantes_screen */}
        {hasSearched && screenState === SCREEN_STATES.RESULTS && (
          <div id="Job-Search-Section" className="results-fade-in">
            <div id="IA-Section" style={{ width: IAButton ? "22%" : "10%" }}>
              <div
                id="Hide-IA-Section"
                onClick={() => setIAButton((prev) => !prev)}
              >
                <MdArrowBackIosNew
                  size={30}
                  color="var(--text-primary)"
                  style={{
                    transform: IAButton ? "rotate(0deg)" : "rotate(180deg)",
                  }}
                />
                {!IAButton ? (
                  <div id="Hide-Screen-IA"></div>
                ) : null}
              </div>
              <div id="IA-Text-Container">
                <Markdown>
                  {ofertas.IA_text}
                </Markdown>
              </div>
            </div>
            <div id="Searching-Message">
              <Map datos={ofertas.Vacantes || mockVacantes} onClick={(oferta) => setOfertaSeleccionada(oferta)} />
            </div>
            <div id="Job-Search-Right-Col">
              <div id="Type-Attachment-Section" className="visible">
                <div
                  id="Text-Container"
                  style={{ backgroundColor: verPagina === SCREEN_STATES2.OFERTA ? "var(--accent-color)" : "" }}
                  onClick={() => setVerPagina(SCREEN_STATES2.OFERTA)}
                >
                  <span id="Texto-Attachment">Oferta</span>
                </div>
                <div
                  id="Text-Container2"
                  style={{ backgroundColor: verPagina === SCREEN_STATES2.PAGINA ? "var(--accent-color)" : "" }}
                  onClick={() => setVerPagina(SCREEN_STATES2.PAGINA)}
                >
                  <span id="Texto-Attachment">Pagina</span>
                </div>
                <div
                  id="Text-Container3"
                  style={{ backgroundColor: verPagina === SCREEN_STATES2.MAPA ? "var(--accent-color)" : "" }}
                  onClick={() => setVerPagina(SCREEN_STATES2.MAPA)}
                >
                  <span id="Texto-Attachment">Mapa</span>
                </div>
              </div>
              {renderOfertas()}
            </div>
          </div>
        )}
      </div>
    );
  };

  return <div id="FrontPanel-Main">{renderContent()}</div>;
}
