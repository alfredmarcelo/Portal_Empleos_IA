import 'leaflet/dist/leaflet.css';
import { useEffect, useState } from 'react';
import './Styles/Apple_map.css';
import { FaWalking, FaCar, FaMotorcycle } from "react-icons/fa";
import Calcular_distancia_metro from './Calcular_distancia_metro';
import Mapa from './Mapa';
import { resolverCoordenadasVacante } from './Coordenadas_vacantes';

const TIPOSRUTA = {
    PIE: 'walking',
    AUTO: 'driving',
    MOTOCICLETA: 'cycling'
};

export default function Apple_map({ ofertaSeleccionada }) {
    const [ruta, setRuta] = useState([]);
    const [minutos, setMinutos] = useState(0);
    const [distancia, setDistancia] = useState(0);
    const [tiporuta, setTiporuta] = useState(TIPOSRUTA.AUTO);
    const [position, setPosition] = useState({
        lat: null,
        lng: null
    });
    const [destino, setDestino] = useState(() => resolverCoordenadasVacante(ofertaSeleccionada?.payload));

    useEffect(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const lat = pos.coords.latitude;
                    const lng = pos.coords.longitude;
                    if (lat && lng) {
                        setPosition({ lat, lng });
                    }
                },
                (err) => {
                    console.log("Geolocalización por defecto en Santo Domingo:", err.message);
                }
            );
        }
    }, []);

    // Actualizar destino cuando cambie la oferta seleccionada
    useEffect(() => {
        if (ofertaSeleccionada?.payload) {
            const coords = resolverCoordenadasVacante(ofertaSeleccionada.payload);
            setDestino(coords);
        }
    }, [ofertaSeleccionada]);

    async function obtenerRutaAPie() {
        try {
            if (!position.lat || !position.lng || !destino.lat || !destino.lng) return [];
            const url =
                `https://router.project-osrm.org/route/v1/${tiporuta}/` +
                `${position.lng},${position.lat};` +
                `${destino.lng},${destino.lat}` +
                '?overview=full&geometries=geojson';

            const res = await fetch(url);
            const data = await res.json();
            if (data?.routes?.[0]) {
                const min = Math.round(data.routes[0].duration / 60);
                const dist = (data.routes[0].distance / 1000).toFixed(1);

                setMinutos(min);
                setDistancia(dist);
                return data.routes[0].geometry.coordinates;
            }
            return [];
        } catch (e) {
            console.warn("No se pudo calcular la ruta en Apple_map:", e);
            return [];
        }
    }

    useEffect(() => {
        if (destino.lat && destino.lng && position.lat && position.lng) {
            obtenerRutaAPie().then(coords => {
                if (coords && coords.length > 0) {
                    setRuta(coords.map(c => [c[1], c[0]]));
                } else {
                    setRuta([]);
                }
            });
        }
    }, [tiporuta, position, destino]);

    return (
        <div id="Job-Search-Frame2">
            <div id="Map-Container">
                <Mapa
                    ruta={ruta}
                    destino={destino}
                    position={position}
                    puesto={ofertaSeleccionada?.payload?.Puesto}
                    parametros={true}
                />
                <div id="Buttons-Container">
                    <div id='Button' onClick={() => setTiporuta(TIPOSRUTA.PIE)} style={{ backgroundColor: tiporuta === 'walking' ? 'grey' : 'var(--job-frame-bg)', borderTopLeftRadius: 10 }}>
                        <FaWalking size={18} style={{ marginRight: 5 }} />
                    </div>
                    <div id='Button' onClick={() => setTiporuta(TIPOSRUTA.AUTO)} style={{ backgroundColor: tiporuta === 'driving' ? 'grey' : 'var(--job-frame-bg)' }}>
                        <FaCar size={18} style={{ marginRight: 5 }} />
                    </div>
                    <div id='Button' onClick={() => setTiporuta(TIPOSRUTA.MOTOCICLETA)} style={{ backgroundColor: tiporuta === 'cycling' ? 'grey' : 'var(--job-frame-bg)', borderTopRightRadius: 10 }}>
                        <FaMotorcycle size={18} style={{ marginRight: 5 }} />
                    </div>
                </div>
            </div>
            <div id="Info-Container">
                <div className="Info-Box">
                    <p>Tiempo Estimado</p>
                    <h3>{minutos} min</h3>
                </div>
                <div className="Info-Box">
                    <p>Distancia</p>
                    <h3>{distancia} km</h3>
                </div>
                <div className="Info-Box">
                    <p>Metro cercano</p>
                    <h3>{Calcular_distancia_metro(destino).replaceAll('_', ' ')}</h3>
                </div>
            </div>
        </div >
    );
}
