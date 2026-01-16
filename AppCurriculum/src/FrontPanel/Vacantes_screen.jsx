import React, { useEffect, useState } from 'react';
import "./Styles/vacantes.css";
import { MdBusiness } from "react-icons/md"; // Icono placeholder para empresa
import Mapas from "./Components/Mapa";

const TIPOSRUTA = {
    PIE: 'walking',
    AUTO: 'driving',
    MOTOCICLETA: 'cycling'
}


export default function Vacantes_screen({ ofertaSeleccionada }) {
    if (!ofertaSeleccionada) return null;

    const { Puesto, Modalidad, Sueldo, Horario, Ubicacion, Descripcion, Beneficios, Direccion } = ofertaSeleccionada.payload;

    const [ruta, setRuta] = useState([]);
    const [minutos, setMinutos] = useState(0);
    const [distancia, setDistancia] = useState(0);
    const [tiporuta, setTiporuta] = useState(TIPOSRUTA.AUTO);
    const [position, setPosition] = useState({
        lat: 0,
        lng: 0
    });
    const [destino, setDestino] = useState({
        lat: 18.48119131912748,
        lng: -69.91720140860824
    });

    useEffect(() => {
        navigator.geolocation.getCurrentPosition((position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            setPosition({ lat, lng });
        });
    }, []);

    async function obtenerRutaAPie() {
        const url =
            `https://router.project-osrm.org/route/v1/${tiporuta}/` +
            `${position.lng},${position.lat};` +
            `${destino.lng},${destino.lat}` +
            '?overview=full&geometries=geojson';

        const res = await fetch(url);
        const data = await res.json();
        const minutos = Math.round(data.routes[0].duration / 60);
        const dist = (data.routes[0].distance / 1000).toFixed(1);

        setMinutos(minutos);
        setDistancia(dist);
        return data.routes[0].geometry.coordinates;
    }



    useEffect(() => {
        obtenerRutaAPie().then(coords => {
            // OSRM → [lng, lat]
            setRuta(coords.map(c => [c[1], c[0]]));
        });
    }, [tiporuta, position]);

    return (
        <div className="Vacantes-Container">

            <div className="Vacantes-Top">
                <div id="Mapa-Container">
                    <div id="Mapa">
                        <Mapas ruta={ruta} destino={destino} position={position} parametros={true} style={{ height: '100%', borderRadius: '10px' }} />
                    </div>
                </div>
                <div className="Vacantes-Info-Container">
                    <div className='Vacantes-Tag-Row'>
                        <h2 className="Vacantes-Title">{Puesto}</h2>
                        <span className="Vacantes-Tag">{Modalidad}</span>
                    </div>

                    <div id="Vacantes-Apply-Container">
                        <div id="Vacantes-Apply-Button" style={{ backgroundColor: "var(--bg-primary)" }}>
                            <text>Aplicar</text>
                        </div>
                        <div id="Vacantes-Apply-Button">
                            <text>Aplicar automatización</text>
                        </div>
                    </div>

                    <div className="Vacantes-Detail-Container">
                        <div className="Vacantes-Detail-Column">
                            <div className="Vacantes-Detail-Row">
                                <span className="Vacantes-Detail-Label">Sueldo:</span>
                                <span className="Vacantes-Detail-Value">{Sueldo}</span>
                            </div>
                            <div className="Vacantes-Detail-Row">
                                <span className="Vacantes-Detail-Label">Horario:</span>
                                <span className="Vacantes-Detail-Value">{Horario}</span>
                            </div>
                            <div className="Vacantes-Detail-Row">
                                <span className="Vacantes-Detail-Label">Ubicación:</span>
                                <span className="Vacantes-Detail-Value">{Ubicacion}</span>
                            </div>
                        </div>
                        <div className="Vacantes-Detail-Column">
                            <div className="Vacantes-Detail-Row">
                                <span className="Vacantes-Detail-Label">Fecha de publicación:</span>
                                <span className="Vacantes-Detail-Value">{new Date().toLocaleDateString()}</span>
                            </div>
                            <div className="Vacantes-Detail-Row">
                                <span className="Vacantes-Detail-Label">Fecha de cierre:</span>
                                <span className="Vacantes-Detail-Value">{new Date().toLocaleDateString()}</span>
                            </div>
                            <div className="Vacantes-Detail-Row">
                                <span className="Vacantes-Detail-Label">Dirección:</span>
                                <span className="Vacantes-Detail-Value">{Direccion}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Mitad Inferior: Descripción */}
            <div className="Vacantes-Bottom">
                {Descripcion && (
                    <div className="Vacantes-Box Vacantes-Description-Box">
                        <h3 className="Vacantes-Section-Title">Descripción</h3>
                        <p className="Vacantes-Text">{Descripcion}</p>
                    </div>
                )}
                {Beneficios && (
                    <div className="Vacantes-Box Vacantes-Benefits-Box">
                        <h3 className="Vacantes-Section-Title">Beneficios</h3>
                        <ul className="Vacantes-Benefits-List">
                            {(Array.isArray(Beneficios) ? Beneficios : Beneficios.split(/\r?\n/)).map((b, i) => (
                                b.trim() !== "" && <li key={i} className="Vacantes-Benefit-Item">{b.trim().replace(/^[-•]\s*/, '')}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}