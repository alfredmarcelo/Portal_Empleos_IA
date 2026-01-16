import { MapContainer, TileLayer, Polyline, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import './Styles/Apple_map.css';

function AjustarVista({ ruta }) {
    const map = useMap();
    if (ruta.length > 0) {
        const bounds = L.latLngBounds(ruta);
        map.fitBounds(bounds);
    }
    return null;
}

export default function Mapa({ ruta, destino, position, style, parametros }) {

    return (
        <MapContainer
            style={style}
            id="Maps"
            {...(parametros === true ? {
                center: [position.lat, position.lng],
                zoom: 13,
                zoomControl: false,
                dragging: false,
                scrollWheelZoom: false,
                doubleClickZoom: false,
                touchZoom: false,
                boxZoom: false,
                keyboard: false,
                maxZoom: 15
            } : {})}
        >
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {ruta.length > 0 && <Polyline positions={ruta} color="red" weight={5} />}
            {ruta.length > 0 && <AjustarVista ruta={ruta} />}
            <Marker position={{ lat: destino.lat, lng: destino.lng }} />
            <Marker position={{ lat: position.lat, lng: position.lng }} />
        </MapContainer>
    );
}