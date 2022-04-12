#version 430
uniform float speed;

layout (local_size_x=128) in;

layout(std430, binding=0) buffer pos{
    vec4 Position[];
};

void main()
{
    uint index = gl_GlobalInvocationID.x;
    vec4 pos = Position[index];
    
    float y = pos.y + pos.x * 0.01 * speed; // integrate
    y = (mod(y+1.0, 2.0)-1.0); //wrap
    Position[index] = vec4(pos.x, y, pos.z, 0.0);   //write back
}