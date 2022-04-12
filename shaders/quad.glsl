#version 330

#if defined VERTEX_SHADER

in vec4 in_position;

out vec3 pos;


void main() {
    vec4 p = in_position;
    gl_Position =  p;
    pos = p.xyz;
}

#elif defined FRAGMENT_SHADER

out vec4 fragColor;

in vec3 pos;
in vec3 normal;
uniform float iTime;
uniform float range;

float gauss(float x, float u, float w)
{
    float y = x - u;
    return exp(-(y*y)/(2*w*w));
}

// Coloured gradient for background
vec4 gradient(vec3 pos)
{
    float p = pos.x;
    vec4 a = vec4(0.0, 0.2, 0.5, 1.0);    
    vec4 c = vec4(0.8, 0.6, 0.0, 1.0) * 0.4;
    float a_w = gauss(p, -0.5, 0.3);
    float b_w = gauss(p, 0.0, 0.05);
    float d_w = gauss(p, 0.0, 0.005);
    float c_w = gauss(p, 0.5, 0.3);
    vec4 base_color =  a_w * a + b_w * c + c_w * a + d_w * vec4(1.0);
    base_color = base_color * (0.9+(0.1*cos(iTime*3+pos.y)));
    return base_color;
}

void main() {
    float rate = pos.x * 100.0;

    // simple vertical gridlines
    float k = 12.0;
    float grid_line = cos(rate) * exp(cos(rate) * k - k);    
    float fade = smoothstep(0.0, 1.0, iTime) + 0.00001 * range;    
    fragColor = fade * gradient(pos)  + grid_line * 0.1;
    fragColor.a = 1.0;
}
#endif
